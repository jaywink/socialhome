import json
from typing import FrozenSet

from channels.generic.websockets import WebsocketConsumer

from socialhome.content.enums import ContentType
from socialhome.content.models import Content


def notify_listeners(content: Content, keys: FrozenSet) -> None:
    """Send out to listening consumers."""
    data = json.dumps({"event": "new", "id": content.id})
    if content.content_type == ContentType.REPLY:
        # Content reply
        StreamConsumer.group_send("streams_content__%s" % content.root_parent.channel_group_name, data)
    # Other pre-calculated notify keys
    for key in keys:
        StreamConsumer.group_send(key, data)


class StreamConsumer(WebsocketConsumer):
    http_user = True
    channel_session_user = True

    def connection_groups(self, **kwargs):
        return ["streams_%s" % kwargs.get("stream")]
