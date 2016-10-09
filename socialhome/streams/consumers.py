import json

from channels.generic.websockets import WebsocketConsumer

from socialhome.publisher.models import Content


class StreamConsumer(WebsocketConsumer):
    http_user = True
    channel_session_user = True

    def connection_groups(self, **kwargs):
        return ["streams_%s" % kwargs.get("stream")]

    def receive(self, text=None, bytes=None, **kwargs):
        data = json.loads(text)
        action = data.get("action")
        if action and action == "load_content":
            self.handle_load_content(data)

    def handle_load_content(self, data):
        """Send back the requested content."""
        ids = data.get("ids")
        if ids:
            contents = Content.get_rendered_contents_for_user(ids, self.message.user)
            payload = json.dumps({
                "event": "content",
                "contents": contents,
            })
            self.send(payload)
