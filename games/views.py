import random
import string

import chess
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.utils import timezone

from accounts.models import Profile
from .engine import apply_move, get_bot_move, legal_moves_for_square, IllegalMoveError
from .models import Game, Move
from .rating import update_ratings_for_game


def home_view(request):
    top_players = Profile.objects.select_related('user').order_by('-rating')[:10]
    active_games = Game.objects.filter(status='active', is_vs_bot=False).count()
    total_players = Profile.objects.count()
    return render(request, 'games/home.html', {
        'top_players': top_players,
        'active_games': active_games,
        'total_players': total_players,
    })


@login_required
def new_bot_game(request, difficulty):
    difficulty = max(1, min(5, int(difficulty)))
    bot_plays = random.choice(['white', 'black'])
    game = Game.objects.create(
        white=request.user if bot_plays == 'black' else None,
        black=request.user if bot_plays == 'white' else None,
        is_vs_bot=True,
        bot_difficulty=difficulty,
        bot_plays=bot_plays,
        status='active',
        started_at=timezone.now(),
    )
    return redirect('games:board', game_id=game.id)


def _gen_invite_code():
    return 'CHESS-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


@login_required
def create_friend_game(request):
    code = _gen_invite_code()
    while Game.objects.filter(invite_code=code).exists():
        code = _gen_invite_code()
    game = Game.objects.create(
        white=request.user,
        is_vs_bot=False,
        status='waiting',
        invite_code=code,
    )
    return redirect('games:board', game_id=game.id)


@login_required
def join_friend_game(request):
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        game = Game.objects.filter(invite_code=code, status='waiting').first()
        if not game:
            return render(request, 'games/join.html', {'error': 'Kod topilmadi yoki o\'yin allaqachon boshlangan.'})
        if game.white_id == request.user.id:
            return render(request, 'games/join.html', {'error': 'Bu o\'zingiz yaratgan o\'yin.'})
        game.black = request.user
        game.status = 'active'
        game.started_at = timezone.now()
        game.save()
        return redirect('games:board', game_id=game.id)
    return render(request, 'games/join.html')


def game_state_view(request, game_id):
    """Lightweight polling endpoint so both players' boards stay in sync
    without WebSockets. Returns current FEN + full move list."""
    game = get_object_or_404(Game, id=game_id)
    moves = [
        {'ply': m.ply, 'san': m.san, 'uci': m.uci}
        for m in game.moves.all()
    ]
    return JsonResponse({
        'ok': True,
        'fen': game.fen,
        'status': game.status,
        'result': game.result,
        'end_reason': game.end_reason,
        'white_time_ms': game.white_time_ms,
        'black_time_ms': game.black_time_ms,
        'moves': moves,
    })


def board_view(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    board = game.board
    user_color = None
    if request.user.is_authenticated:
        if game.white_id == request.user.id:
            user_color = 'white'
        elif game.black_id == request.user.id:
            user_color = 'black'
    return render(request, 'games/board.html', {
        'game': game,
        'legal_fen': game.fen,
        'user_color': user_color,
        'is_check': board.is_check(),
        'moves': game.moves.all(),
    })


def legal_moves_view(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    square = request.GET.get('square')
    if not square:
        return JsonResponse({'ok': False, 'error': 'square required'}, status=400)
    try:
        moves = legal_moves_for_square(game.fen, square)
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'invalid square'}, status=400)
    return JsonResponse({'ok': True, 'moves': moves})


@login_required
@require_POST
def make_move(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if game.status != 'active':
        return JsonResponse({'ok': False, 'error': 'O\'yin faol emas'}, status=400)

    user_color = 'white' if game.white_id == request.user.id else (
        'black' if game.black_id == request.user.id else None
    )
    if user_color is None:
        return JsonResponse({'ok': False, 'error': 'Siz bu o\'yin ishtirokchisi emassiz'}, status=403)
    if user_color != game.turn_color():
        return JsonResponse({'ok': False, 'error': 'Sizning navbatingiz emas'}, status=400)

    move_uci = request.POST.get('move')
    try:
        result = apply_move(game.fen, move_uci)
    except IllegalMoveError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

    ply = game.moves.count() + 1
    Move.objects.create(
        game=game, ply=ply, san=result['san'], uci=result['uci'],
        fen_after=result['fen'], played_by=request.user, is_bot_move=False,
    )
    game.fen = result['fen']

    bot_move_data = None
    if result['game_over']:
        _finish_game(game, result['result'], result['end_reason'])
    else:
        game.save()
        if game.is_vs_bot and game.turn_color() == game.bot_plays:
            bot_move_data = _play_bot_move(game)

    game.refresh_from_db()
    return JsonResponse({
        'ok': True,
        'fen': game.fen,
        'san': result['san'],
        'uci': result['uci'],
        'is_check': result['is_check'],
        'game_over': game.status == 'finished',
        'result': game.result,
        'end_reason': game.end_reason,
        'bot_move': bot_move_data,
    })


def _play_bot_move(game):
    bot_uci = get_bot_move(game.fen, difficulty=game.bot_difficulty)
    result = apply_move(game.fen, bot_uci)
    ply = game.moves.count() + 1
    Move.objects.create(
        game=game, ply=ply, san=result['san'], uci=result['uci'],
        fen_after=result['fen'], played_by=None, is_bot_move=True,
    )
    game.fen = result['fen']
    if result['game_over']:
        _finish_game(game, result['result'], result['end_reason'])
    else:
        game.save()
    return {
        'uci': result['uci'], 'san': result['san'], 'fen': result['fen'],
        'is_check': result['is_check'], 'game_over': result['game_over'],
    }


def _finish_game(game, result, end_reason):
    game.status = 'finished'
    game.result = result
    game.end_reason = end_reason
    game.finished_at = timezone.now()
    game.save()
    if not game.is_vs_bot and game.white_id and game.black_id:
        update_ratings_for_game(game)
    elif game.is_vs_bot:
        _update_stats_vs_bot(game)


def _update_stats_vs_bot(game):
    human_user = game.white if game.bot_plays == 'black' else game.black
    if not human_user:
        return
    profile, _ = Profile.objects.get_or_create(user=human_user)
    human_color = 'black' if game.bot_plays == 'white' else 'white'
    if game.result == 'draw':
        profile.draws += 1
    elif game.result == human_color:
        profile.wins += 1
    else:
        profile.losses += 1
    profile.save()


@login_required
@require_POST
def resign_game(request, game_id):
    game = get_object_or_404(Game, id=game_id)
    if game.status != 'active':
        return JsonResponse({'ok': False, 'error': 'O\'yin faol emas'}, status=400)
    user_color = 'white' if game.white_id == request.user.id else (
        'black' if game.black_id == request.user.id else None
    )
    if user_color is None:
        return JsonResponse({'ok': False, 'error': 'Ruxsat yo\'q'}, status=403)
    winner = 'black' if user_color == 'white' else 'white'
    _finish_game(game, winner, 'resignation')
    return JsonResponse({'ok': True, 'result': winner, 'end_reason': 'resignation'})


def leaderboard_view(request):
    players = Profile.objects.select_related('user').order_by('-rating')[:50]
    return render(request, 'games/leaderboard.html', {'players': players})
