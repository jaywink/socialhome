import json
from typing import Set

from channels.generic.websockets import WebsocketConsumer

from socialhome.content.models import Content


def notify_listeners(content: Content, keys: Set) -> None:
    """Send out to listening consumers."""
    data = json.dumps({"event": "new", "id": content.id})
    for key in keys:
        StreamConsumer.group_send(key, data)


class StreamConsumer(WebsocketConsumer):
    http_user = True
    channel_session_user = True

    def connection_groups(self, **kwargs):
        return ["streams_%s" % kwargs.get("stream")]
