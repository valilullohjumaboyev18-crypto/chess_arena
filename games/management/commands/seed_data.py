import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile
from games.models import Game

NAMES = ['magnus', 'hikaru', 'fabiano', 'ding', 'nepo', 'anish', 'wesley',
         'alireza', 'levon', 'shakhriyor', 'nodirbek', 'javokhir', 'sardor', 'aziz']


class Command(BaseCommand):
    help = 'Seed demo users, profiles and games'

    def handle(self, *args, **options):
        created = 0
        for name in NAMES:
            user, was_created = User.objects.get_or_create(
                username=name, defaults={'email': f'{name}@example.com'}
            )
            if was_created:
                user.set_password('password123')
                user.save()
                created += 1
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.rating = random.randint(900, 2400)
            profile.wins = random.randint(0, 40)
            profile.losses = random.randint(0, 40)
            profile.draws = random.randint(0, 10)
            profile.save()

        users = list(User.objects.filter(username__in=NAMES))
        games_created = 0
        for _ in range(8):
            w, b = random.sample(users, 2)
            result = random.choice(['white', 'black', 'draw'])
            Game.objects.create(
                white=w, black=b, status='finished', result=result,
                end_reason='checkmate' if result != 'draw' else 'stalemate',
            )
            games_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seed complete: {created} new users, {games_created} demo games. '
            f'Password for all demo users: password123'
        ))
