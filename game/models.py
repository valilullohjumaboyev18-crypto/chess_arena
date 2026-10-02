import uuid
from django.db import models

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

MODE_CHOICES = [
    ("bot", "Bot bilan"),
    ("local", "Ikki kishilik (bitta qurilma)"),
    ("friend", "Do'st bilan (onlayn)"),
    ("tournament", "Musobaqa"),
]

DIFFICULTY_CHOICES = [
    ("easy", "Kuchsiz"),
    ("medium", "O'rta"),
    ("hard", "Kuchli"),
]

STATUS_CHOICES = [
    ("waiting", "Kutilmoqda"),
    ("ongoing", "Davom etmoqda"),
    ("finished", "Tugagan"),
]


class Game(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    fen = models.CharField(max_length=100, default=START_FEN)
    move_history = models.TextField(blank=True, default="")  # SAN moves space separated
    uci_history = models.TextField(blank=True, default="")   # uci moves space separated

    white_session = models.CharField(max_length=64, blank=True, default="")
    white_name = models.CharField(max_length=40, blank=True, default="Oq")
    black_session = models.CharField(max_length=64, blank=True, default="")
    black_name = models.CharField(max_length=40, blank=True, default="Qora")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="waiting")
    result = models.CharField(max_length=10, blank=True, default="")  # "1-0","0-1","1/2-1/2"
    result_reason = models.CharField(max_length=40, blank=True, default="")

    bot_difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, blank=True, default="")
    bot_color = models.CharField(max_length=5, blank=True, default="")  # "white" or "black"

    tournament_match = models.OneToOneField(
        "TournamentMatch", null=True, blank=True, on_delete=models.SET_NULL, related_name="game"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def turn(self):
        return "white" if " w " in f" {self.fen} " else "black"

    def __str__(self):
        return f"Game {self.id} ({self.mode})"


class Tournament(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=80)
    creator_name = models.CharField(max_length=40)
    creator_session = models.CharField(max_length=64)
    max_players = models.IntegerField(default=8)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="waiting")
    winner_name = models.CharField(max_length=40, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TournamentPlayer(models.Model):
    tournament = models.ForeignKey(Tournament, related_name="players", on_delete=models.CASCADE)
    name = models.CharField(max_length=40)
    session = models.CharField(max_length=64)
    seed = models.IntegerField()
    eliminated = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["seed"]

    def __str__(self):
        return self.name


class TournamentMatch(models.Model):
    tournament = models.ForeignKey(Tournament, related_name="matches", on_delete=models.CASCADE)
    round_number = models.IntegerField()
    position = models.IntegerField()
    player1 = models.ForeignKey(
        TournamentPlayer, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    player2 = models.ForeignKey(
        TournamentPlayer, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    winner = models.ForeignKey(
        TournamentPlayer, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    is_bye = models.BooleanField(default=False)

    class Meta:
        ordering = ["round_number", "position"]

    def __str__(self):
        return f"R{self.round_number}#{self.position}"
