import json
from typing import Set

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer

from socialhome.content.models import Content


def notify_listeners(content: Content, keys: Set) -> None:
    """Send out to listening consumers."""
    channel_layer = get_channel_layer()
    data = {"type": "notification", "payload": {"event": "new", "id": content.id,
        "parentId": getattr(content.parent, 'id', None)}}
    for key in keys:
        async_to_sync(channel_layer.group_send)(key, data)


class StreamConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)(self.get_stream_name(), self.channel_name)
        user = self.scope["user"]
        if user and user.is_authenticated:
            async_to_sync(user.mark_recently_active())
        super().connect()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.get_stream_name(), self.channel_name)
        super().disconnect(code)

    def get_stream_name(self) -> str:
        return f"streams_{self.scope['url_route']['kwargs']['stream']}"

    def notification(self, event):
        self.send(text_data=json.dumps(event["payload"]))

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        if data.get("event") == "ping":
            user = self.scope["user"]
            if user and user.is_authenticated:
                async_to_sync(user.mark_recently_active())
