from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/multiplayer/(?P<room_id>\w+)/$', consumers.MultiplayerConsumer.as_asgi()),
    re_path(r'ws/global-chat/$', consumers.GlobalChatConsumer.as_asgi()),
]
