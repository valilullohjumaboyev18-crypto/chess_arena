from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.models import User

from games.models import Game
from .forms import RegisterForm
from .models import Profile


def register_view(request):
    if request.user.is_authenticated:
        return redirect('games:home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('games:home')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


class ChessLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class ChessLogoutView(LogoutView):
    next_page = 'games:home'


def profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile, _ = Profile.objects.get_or_create(user=user)
    games = Game.objects.filter(status='finished').filter(
        white=user
    ) | Game.objects.filter(status='finished').filter(black=user)
    games = games.distinct().order_by('-finished_at')[:20]
    return render(request, 'accounts/profile.html', {
        'profile_user': user,
        'profile': profile,
        'games': games,
    })


@login_required
def dashboard_view(request):
    return redirect('accounts:profile', username=request.user.username)
