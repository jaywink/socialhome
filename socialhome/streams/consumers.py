import json
from typing import Set, Union

from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

from socialhome.content.models import Content
from socialhome.users.models import Profile


channel_layer = get_channel_layer()
def notify_listeners(obj: Union[Content, Profile], keys: Set, event: str = "new") -> None:
    """Send out to listening consumers."""
    payload = {"event": event}
    if event == 'profile':
        payload.update({'uuid': str(obj.uuid)})
    else:
        payload.update({"id": obj.id, "parentId": getattr(obj.parent, 'id', None)})

    data = {"type": "notification", "payload": payload}
    for key in keys:
        async_to_sync(channel_layer.group_send)(key, data)
        #await channel_layer.group_send(key, data)

class StreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(self.get_stream_name(), self.channel_name)
        user = self.scope["user"]
        if user and user.is_authenticated:
            user.mark_recently_active()
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.get_stream_name(), self.channel_name)
        #await super().disconnect(code)

    def get_stream_name(self) -> str:
        return f"streams_{self.scope['url_route']['kwargs']['stream']}"

    async def notification(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        if data.get("event") == "ping":
            await self.send(text_data=json.dumps({"event": "pong"}))
            user = self.scope["user"]
            if user and user.is_authenticated:
                user.mark_recently_active()
