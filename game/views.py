import json
import uuid
import chess

from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Game, Tournament, TournamentPlayer, TournamentMatch, START_FEN
from . import engine, bracket


def get_session_id(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def home(request):
    return render(request, "game/home.html")


# ---------------------------------------------------------------- BOT MODE
def bot_new(request):
    if request.method == "POST":
        difficulty = request.POST.get("difficulty", "medium")
        color = request.POST.get("color", "white")
        sid = get_session_id(request)
        player_name = request.POST.get("name") or "Siz"

        game = Game.objects.create(
            mode="bot",
            status="ongoing",
            bot_difficulty=difficulty,
            bot_color="black" if color == "white" else "white",
        )
        if color == "white":
            game.white_session, game.white_name = sid, player_name
            game.black_name = "Bot"
        else:
            game.black_session, game.black_name = sid, player_name
            game.white_name = "Bot"
        game.save()

        if game.bot_color == "white":
            _apply_bot_move(game)
        return redirect("game_detail", game_id=game.id)
    return render(request, "game/bot_new.html")


# ---------------------------------------------------------------- LOCAL MODE
def local_new(request):
    sid = get_session_id(request)
    game = Game.objects.create(
        mode="local",
        status="ongoing",
        white_session=sid, white_name="Oq",
        black_session=sid, black_name="Qora",
    )
    return redirect("game_detail", game_id=game.id)


# ---------------------------------------------------------------- FRIEND MODE
def friend_new(request):
    if request.method == "POST":
        sid = get_session_id(request)
        name = request.POST.get("name") or "O'yinchi 1"
        game = Game.objects.create(
            mode="friend",
            status="waiting",
            white_session=sid,
            white_name=name,
        )
        return redirect("game_detail", game_id=game.id)
    return render(request, "game/friend_new.html")


def friend_join(request, game_id):
    game = get_object_or_404(Game, id=game_id, mode="friend")
    sid = get_session_id(request)
    if game.status == "waiting" and sid != game.white_session:
        if request.method == "POST":
            name = request.POST.get("name") or "O'yinchi 2"
            game.black_session = sid
            game.black_name = name
            game.status = "ongoing"
            game.save()
            return redirect("game_detail", game_id=game.id)
        return render(request, "game/friend_join.html", {"game": game})
    return redirect("game_detail", game_id=game.id)


# ---------------------------------------------------------------- GAME PLAY
def game_detail(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    sid = get_session_id(request)

    if game.mode == "friend" and game.status == "waiting" and sid != game.white_session:
        return redirect("friend_join", game_id=game.id)

    my_color = None
    if sid == game.white_session:
        my_color = "white"
    if sid == game.black_session:
        my_color = "black" if my_color is None else "both"
    if game.mode == "local":
        my_color = "both"

    share_url = request.build_absolute_uri(f"/game/{game.id}/join/") if game.mode == "friend" else None

    return render(request, "game/board.html", {
        "game": game,
        "my_color": my_color,
        "share_url": share_url,
    })


def game_state(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    return JsonResponse(_game_state_payload(game))


def _game_state_payload(game):
    board = chess.Board(game.fen)
    return {
        "fen": game.fen,
        "turn": "white" if board.turn == chess.WHITE else "black",
        "status": game.status,
        "result": game.result,
        "result_reason": game.result_reason,
        "white_name": game.white_name,
        "black_name": game.black_name,
        "move_history": game.move_history.split() if game.move_history else [],
        "in_check": board.is_check(),
        "legal_moves": [m.uci() for m in board.legal_moves] if game.status == "ongoing" else [],
    }


@require_POST
def make_move(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    sid = get_session_id(request)

    if game.status != "ongoing":
        return JsonResponse({"error": "O'yin tugagan"}, status=400)

    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        return HttpResponseBadRequest("Noto'g'ri so'rov")

    uci_move = data.get("move")
    promotion = data.get("promotion")
    board = chess.Board(game.fen)

    mover_color = "white" if board.turn == chess.WHITE else "black"
    if game.mode != "local":
        allowed_session = game.white_session if mover_color == "white" else game.black_session
        if sid != allowed_session:
            return JsonResponse({"error": "Bu sizning navbatingiz emas"}, status=403)

    try:
        move = chess.Move.from_uci(uci_move)
    except ValueError:
        return JsonResponse({"error": "Noto'g'ri yurish formati"}, status=400)

    if move not in board.legal_moves:
        return JsonResponse({"error": "Qonunga xilof yurish"}, status=400)

    san = board.san(move)
    board.push(move)
    game.fen = board.fen()
    game.move_history = (game.move_history + " " + san).strip()
    game.uci_history = (game.uci_history + " " + uci_move).strip()
    _check_game_over(game, board)
    game.save()

    if game.status == "ongoing" and game.mode == "bot":
        bot_turn_color = game.bot_color
        current_turn = "white" if board.turn == chess.WHITE else "black"
        if current_turn == bot_turn_color:
            _apply_bot_move(game)

    if game.status == "finished" and game.mode == "tournament" and game.tournament_match:
        _resolve_tournament_game(game)

    return JsonResponse(_game_state_payload(game))


def _apply_bot_move(game):
    bot_uci = engine.choose_bot_move(game.fen, game.bot_difficulty or "medium")
    if not bot_uci:
        return
    board = chess.Board(game.fen)
    move = chess.Move.from_uci(bot_uci)
    san = board.san(move)
    board.push(move)
    game.fen = board.fen()
    game.move_history = (game.move_history + " " + san).strip()
    game.uci_history = (game.uci_history + " " + bot_uci).strip()
    _check_game_over(game, board)
    game.save()


def _check_game_over(game, board):
    if board.is_checkmate():
        game.status = "finished"
        game.result = "0-1" if board.turn == chess.WHITE else "1-0"
        game.result_reason = "mat"
    elif board.is_stalemate():
        game.status = "finished"
        game.result = "1/2-1/2"
        game.result_reason = "pat"
    elif board.is_insufficient_material():
        game.status = "finished"
        game.result = "1/2-1/2"
        game.result_reason = "yetarli material yo'q"
    elif board.can_claim_fifty_moves():
        game.status = "finished"
        game.result = "1/2-1/2"
        game.result_reason = "50 yurish qoidasi"
    elif board.is_repetition(3):
        game.status = "finished"
        game.result = "1/2-1/2"
        game.result_reason = "takrorlanish"


def _resolve_tournament_game(game):
    match = game.tournament_match
    if match.winner:
        return
    if game.result == "1-0":
        winner_session, winner_name = game.white_session, game.white_name
    elif game.result == "0-1":
        winner_session, winner_name = game.black_session, game.black_name
    else:
        # durang bo'lsa - qora tosh bilan o'ynagan (ko'proq qiyinchilikda bo'lgan) g'olib deb belgilanadi
        winner_session, winner_name = game.black_session, game.black_name

    winner = match.player1 if match.player1 and match.player1.session == winner_session else match.player2
    if winner is None:
        winner = match.player1 or match.player2
    bracket.record_match_winner(match, winner)


# ---------------------------------------------------------------- TOURNAMENT
def tournament_new(request):
    if request.method == "POST":
        sid = get_session_id(request)
        name = request.POST.get("tname") or "Musobaqa"
        creator = request.POST.get("name") or "Tashkilotchi"
        size = int(request.POST.get("size", 8))

        t = Tournament.objects.create(
            name=name, creator_name=creator, creator_session=sid, max_players=size,
        )
        TournamentPlayer.objects.create(tournament=t, name=creator, session=sid, seed=1)
        return redirect("tournament_lobby", t_id=t.id)
    return render(request, "game/tournament_new.html")


def tournament_lobby(request, t_id):
    t = get_object_or_404(Tournament, id=t_id)
    sid = get_session_id(request)
    is_creator = sid == t.creator_session
    joined = t.players.filter(session=sid).exists()
    share_url = request.build_absolute_uri(f"/tournament/{t.id}/join/")

    if t.status != "waiting":
        return redirect("tournament_bracket", t_id=t.id)

    return render(request, "game/tournament_lobby.html", {
        "t": t, "is_creator": is_creator, "joined": joined, "share_url": share_url,
    })


def tournament_join(request, t_id):
    t = get_object_or_404(Tournament, id=t_id)
    sid = get_session_id(request)

    if t.status != "waiting":
        return redirect("tournament_bracket", t_id=t.id)

    already = t.players.filter(session=sid).exists()
    if already:
        return redirect("tournament_lobby", t_id=t.id)

    if request.method == "POST":
        name = request.POST.get("name") or "O'yinchi"
        if t.players.count() < t.max_players:
            seed = t.players.count() + 1
            TournamentPlayer.objects.create(tournament=t, name=name, session=sid, seed=seed)
        return redirect("tournament_lobby", t_id=t.id)

    return render(request, "game/tournament_join.html", {"t": t})


@require_POST
def tournament_start(request, t_id):
    t = get_object_or_404(Tournament, id=t_id)
    sid = get_session_id(request)
    if sid != t.creator_session or t.status != "waiting":
        return redirect("tournament_lobby", t_id=t.id)
    bracket.start_tournament(t)
    return redirect("tournament_bracket", t_id=t.id)


def tournament_bracket(request, t_id):
    t = get_object_or_404(Tournament, id=t_id)
    sid = get_session_id(request)

    rounds = {}
    for m in t.matches.select_related("player1", "player2", "winner").order_by("round_number", "position"):
        rounds.setdefault(m.round_number, []).append(m)

    my_active_game = None
    if t.status == "ongoing":
        for m in t.matches.filter(winner__isnull=True, is_bye=False):
            game = getattr(m, "game", None)
            if game and sid in (game.white_session, game.black_session):
                my_active_game = game
                break

    return render(request, "game/tournament_bracket.html", {
        "t": t, "rounds": sorted(rounds.items()), "my_active_game": my_active_game,
    })


def tournament_state(request, t_id):
    """Lobby/bracket sahifalari uchun yengil poll endpoint."""
    t = get_object_or_404(Tournament, id=t_id)
    players = list(t.players.values_list("name", flat=True))
    return JsonResponse({
        "status": t.status,
        "players": players,
        "count": len(players),
        "max_players": t.max_players,
        "winner_name": t.winner_name,
    })
