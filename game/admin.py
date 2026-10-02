from django.contrib import admin
from .models import Game, Tournament, TournamentPlayer, TournamentMatch

admin.site.register(Game)
admin.site.register(Tournament)
admin.site.register(TournamentPlayer)
admin.site.register(TournamentMatch)
