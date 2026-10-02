from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("bot/new/", views.bot_new, name="bot_new"),
    path("local/new/", views.local_new, name="local_new"),
    path("friend/new/", views.friend_new, name="friend_new"),
    path("game/<uuid:game_id>/join/", views.friend_join, name="friend_join"),

    path("game/<uuid:game_id>/", views.game_detail, name="game_detail"),
    path("game/<uuid:game_id>/state/", views.game_state, name="game_state"),
    path("game/<uuid:game_id>/move/", views.make_move, name="make_move"),

    path("tournament/new/", views.tournament_new, name="tournament_new"),
    path("tournament/<uuid:t_id>/", views.tournament_lobby, name="tournament_lobby"),
    path("tournament/<uuid:t_id>/join/", views.tournament_join, name="tournament_join"),
    path("tournament/<uuid:t_id>/start/", views.tournament_start, name="tournament_start"),
    path("tournament/<uuid:t_id>/bracket/", views.tournament_bracket, name="tournament_bracket"),
    path("tournament/<uuid:t_id>/state/", views.tournament_state, name="tournament_state"),
]
