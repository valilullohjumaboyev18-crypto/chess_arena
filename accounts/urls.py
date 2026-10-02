from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.ChessLoginView.as_view(), name='login'),
    path('logout/', views.ChessLogoutView.as_view(), name='logout'),
    path('me/', views.dashboard_view, name='dashboard'),
    path('u/<str:username>/', views.profile_view, name='profile'),
]
