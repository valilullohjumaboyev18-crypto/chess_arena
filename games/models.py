import chess

from django.conf import settings
from django.db import models

STARTING_FEN = chess.STARTING_FEN

TIME_CONTROLS = [
    ('1+0', 'Bullet 1+0'),
    ('3+2', 'Blitz 3+2'),
    ('5+0', 'Blitz 5+0'),
    ('10+0', 'Rapid 10+0'),
    ('30+0', 'Classical 30+0'),
]

BOT_DIFFICULTY = [
    (1, 'Beginner'),
    (2, 'Easy'),
    (3, 'Medium'),
    (4, 'Hard'),
    (5, 'Expert'),
]

RESULT_CHOICES = [
    ('white', 'White won'),
    ('black', 'Black won'),
    ('draw', 'Draw'),
    ('*', 'In progress'),
]

END_REASON_CHOICES = [
    ('checkmate', 'Checkmate'),
    ('resignation', 'Resignation'),
    ('timeout', 'Timeout'),
    ('stalemate', 'Stalemate'),
    ('threefold', 'Threefold repetition'),
    ('insufficient_material', 'Insufficient material'),
    ('fifty_moves', 'Fifty-move rule'),
    ('draw_agreement', 'Draw agreed'),
    ('', ''),
]


class Game(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Waiting for opponent'),
        ('active', 'Active'),
        ('finished', 'Finished'),
        ('aborted', 'Aborted'),
    ]

    white = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='games_as_white',
        on_delete=models.CASCADE, null=True, blank=True,
    )
    black = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='games_as_black',
        on_delete=models.CASCADE, null=True, blank=True,
    )
    is_vs_bot = models.BooleanField(default=False)
    bot_difficulty = models.IntegerField(choices=BOT_DIFFICULTY, default=3)
    bot_plays = models.CharField(
        max_length=5, choices=[('white', 'white'), ('black', 'black')], default='black'
    )

    fen = models.CharField(max_length=100, default=STARTING_FEN)
    pgn = models.TextField(blank=True, default='')

    time_control = models.CharField(max_length=10, choices=TIME_CONTROLS, default='10+0')
    white_time_ms = models.IntegerField(default=600000)
    black_time_ms = models.IntegerField(default=600000)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='waiting')
    result = models.CharField(max_length=5, choices=RESULT_CHOICES, default='*')
    end_reason = models.CharField(max_length=25, choices=END_REASON_CHOICES, blank=True, default='')

    invite_code = models.CharField(max_length=20, unique=True, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Game #{self.pk} ({self.status})'

    @property
    def board(self):
        return chess.Board(self.fen)

    def turn_color(self):
        return 'white' if self.board.turn == chess.WHITE else 'black'


class Move(models.Model):
    game = models.ForeignKey(Game, related_name='moves', on_delete=models.CASCADE)
    ply = models.PositiveIntegerField()
    san = models.CharField(max_length=10)
    uci = models.CharField(max_length=10)
    fen_after = models.CharField(max_length=100)
    played_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    is_bot_move = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ply']
        unique_together = ('game', 'ply')

    def __str__(self):
        return f'{self.game_id}#{self.ply}: {self.san}'
