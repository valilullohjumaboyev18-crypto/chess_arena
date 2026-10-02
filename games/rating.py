"""Server-side ELO rating calculation. Client can never influence this."""
from accounts.models import Profile

K_FACTOR = 32


def _expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def update_ratings_for_game(game):
    white_profile, _ = Profile.objects.get_or_create(user=game.white)
    black_profile, _ = Profile.objects.get_or_create(user=game.black)

    if game.result == 'white':
        score_white, score_black = 1, 0
        white_profile.wins += 1
        black_profile.losses += 1
    elif game.result == 'black':
        score_white, score_black = 0, 1
        white_profile.losses += 1
        black_profile.wins += 1
    else:
        score_white, score_black = 0.5, 0.5
        white_profile.draws += 1
        black_profile.draws += 1

    expected_white = _expected_score(white_profile.rating, black_profile.rating)
    expected_black = _expected_score(black_profile.rating, white_profile.rating)

    white_profile.rating = round(white_profile.rating + K_FACTOR * (score_white - expected_white))
    black_profile.rating = round(black_profile.rating + K_FACTOR * (score_black - expected_black))

    white_profile.save()
    black_profile.save()
