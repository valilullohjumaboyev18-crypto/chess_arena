from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile'
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    rating = models.IntegerField(default=1200)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} ({self.rating})'

    @property
    def games_played(self):
        return self.wins + self.losses + self.draws

    @property
    def win_rate(self):
        total = self.games_played
        if total == 0:
            return 0
        return round(self.wins / total * 100, 1)
