from django.urls import path
from . import views

app_name = 'wordchain'

urlpatterns = [
    path('', views.index, name='index'),
    path('start/', views.start_game, name='start_game'),
    path('submit/', views.submit_word, name='submit_word'),
    path('history/', views.game_history, name='game_history'),
]
