"""Yagona eliminatsiya (single-elimination) turnir bracket mantiqi."""
import math
from .models import Tournament, TournamentMatch, TournamentPlayer, Game


def next_power_of_two(n):
    return 1 if n <= 1 else 2 ** math.ceil(math.log2(n))


def start_tournament(tournament: Tournament):
    """Qo'shilgan o'yinchilar bo'yicha 1-raundni yaratadi. Toq son bo'lsa, bye beriladi."""
    players = list(tournament.players.filter(eliminated=False).order_by("seed"))
    if len(players) < 2:
        return False

    size = next_power_of_two(len(players))
    # bo'sh joylarni None (bye) bilan to'ldiramiz
    slots = players + [None] * (size - len(players))

    for i in range(0, size, 2):
        p1, p2 = slots[i], slots[i + 1]
        match = TournamentMatch.objects.create(
            tournament=tournament,
            round_number=1,
            position=i // 2,
            player1=p1,
            player2=p2,
            is_bye=(p1 is None or p2 is None),
        )
        if match.is_bye:
            winner = p1 or p2
            match.winner = winner
            match.save()
        else:
            game = Game.objects.create(
                mode="tournament",
                white_session=p1.session,
                white_name=p1.name,
                black_session=p2.session,
                black_name=p2.name,
                status="ongoing",
                tournament_match=match,
            )

    tournament.status = "ongoing"
    tournament.save()
    return True


def record_match_winner(match: TournamentMatch, winner: TournamentPlayer):
    match.winner = winner
    match.save()
    loser = match.player2 if match.player1_id == winner.id else match.player1
    if loser:
        loser.eliminated = True
        loser.save()
    maybe_advance_round(match.tournament)


def maybe_advance_round(tournament: Tournament):
    current_round = tournament.matches.order_by("-round_number").first()
    if current_round is None:
        return
    round_number = current_round.round_number
    matches = list(tournament.matches.filter(round_number=round_number).order_by("position"))
    if any(m.winner is None for m in matches):
        return  # raund hali tugamagan

    winners = [m.winner for m in matches]
    if len(winners) == 1:
        tournament.status = "finished"
        tournament.winner_name = winners[0].name if winners[0] else ""
        tournament.save()
        return

    next_round = round_number + 1
    for i in range(0, len(winners), 2):
        p1 = winners[i]
        p2 = winners[i + 1] if i + 1 < len(winners) else None
        match = TournamentMatch.objects.create(
            tournament=tournament,
            round_number=next_round,
            position=i // 2,
            player1=p1,
            player2=p2,
            is_bye=(p2 is None),
        )
        if match.is_bye:
            match.winner = p1
            match.save()
        else:
            Game.objects.create(
                mode="tournament",
                white_session=p1.session,
                white_name=p1.name,
                black_session=p2.session,
                black_name=p2.name,
                status="ongoing",
                tournament_match=match,
            )
    # agar navbatdagi raund ham to'liq bye lardan iborat bo'lsa, rekursiv tekshiramiz
    maybe_advance_round(tournament)
