from django.urls import path
from . import views

app_name = 'baseball'

urlpatterns = [
    path('', views.index, name='index'),
    path('start/', views.start_game, name='start_game'),
    path('guess/', views.make_guess, name='make_guess'),
    path('status/<int:game_id>/', views.game_status, name='game_status'),
    path('restart/', views.restart_game, name='restart_game'),
    path('history/', views.game_history, name='game_history'),
    path('ai-stats/', views.get_ai_statistics, name='ai_statistics'),
]
