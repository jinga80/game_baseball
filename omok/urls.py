from django.urls import path
from . import views

app_name = 'omok'

urlpatterns = [
    path('', views.index, name='index'),
    path('start/', views.start_game, name='start_game'),
    path('move/', views.make_move, name='make_move'),
    path('history/', views.game_history, name='game_history'),
]
