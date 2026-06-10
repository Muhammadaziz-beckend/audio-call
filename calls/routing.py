from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Диспетчер
    re_path(r"^ws/calls/(?P<type>dispatch)/$", consumers.SignalingConsumer.as_asgi()),
    # Менеджер
    re_path(r"^ws/calls/(?P<type>manager)/(?P<manager_id>\d+)/$", consumers.SignalingConsumer.as_asgi()),
    # WebRTC комната
    re_path(r"^ws/calls/(?P<type>room)/(?P<room_id>[^/]+)/$", consumers.SignalingConsumer.as_asgi()),
]
