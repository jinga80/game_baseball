from django.urls import path
from . import views

app_name = 'multiplayer'

urlpatterns = [
    path('', views.index, name='index'),
    path('create-room/', views.create_room, name='create_room'),
    path('join-room/', views.join_room, name='join_room'),
    path('room-list/', views.get_room_list, name='room_list'),
    path('room/<uuid:room_id>/', views.get_room_info, name='room_info'),
    path('send-message/', views.send_message, name='send_message'),
    path('leave-room/', views.leave_room, name='leave_room'),
    path('start-game/', views.start_game, name='start_game'),
    path('toggle-ready/', views.toggle_ready, name='toggle_ready'),
]
