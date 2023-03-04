# TODO: remove this file when ASGI has been run for a while
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

from socialhome.streams.consumers import StreamConsumer

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ch/streams/<str:stream>/", StreamConsumer),
        ])
    ),
})
