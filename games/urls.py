from django.urls import path

from . import views

app_name = 'games'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('bot/<int:difficulty>/', views.new_bot_game, name='new_bot_game'),
    path('friend/create/', views.create_friend_game, name='create_friend_game'),
    path('friend/join/', views.join_friend_game, name='join_friend_game'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('<int:game_id>/', views.board_view, name='board'),
    path('<int:game_id>/state/', views.game_state_view, name='game_state'),
    path('<int:game_id>/legal-moves/', views.legal_moves_view, name='legal_moves'),
    path('<int:game_id>/move/', views.make_move, name='make_move'),
    path('<int:game_id>/resign/', views.resign_game, name='resign'),
]
