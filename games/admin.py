from django.contrib import admin

from .models import Game, Move


class MoveInline(admin.TabularInline):
    model = Move
    extra = 0
    readonly_fields = ('ply', 'san', 'uci', 'played_by', 'is_bot_move', 'created_at')


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('id', 'white', 'black', 'is_vs_bot', 'status', 'result', 'time_control', 'created_at')
    list_filter = ('status', 'is_vs_bot', 'result', 'time_control')
    search_fields = ('white__username', 'black__username', 'invite_code')
    inlines = [MoveInline]


@admin.register(Move)
class MoveAdmin(admin.ModelAdmin):
    list_display = ('game', 'ply', 'san', 'played_by', 'is_bot_move')
    list_filter = ('is_bot_move',)
