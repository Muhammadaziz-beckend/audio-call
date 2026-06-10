"""
asgi.py — замени содержимое своего project/asgi.py на этот файл.
"""
import os

# ВАЖНО: должно быть до всех django-импортов
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from calls.routing import websocket_urlpatterns

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    }
)
