import json

from channels.generic.websockets import WebsocketConsumer

from socialhome.content.models import Content


class StreamConsumer(WebsocketConsumer):
    http_user = True
    channel_session_user = True

    def connection_groups(self, **kwargs):
        return ["streams_%s" % kwargs.get("stream")]

    def receive(self, text=None, bytes=None, **kwargs):
        data = json.loads(text)
        action = data.get("action")
        if not action:
            return
        if action == "load_content":
            self.handle_load_content(data)
        elif action == "load_more":
            self.handle_load_more(data)

    def handle_load_content(self, data):
        """Send back the requested content."""
        # TODO handle load according to stream qs - not public
        ids = data.get("ids")
        if not ids:
            return
        qs = Content.objects.filter(id__in=ids)
        qs = Content.filter_for_user(qs, self.message.user).order_by("-created")
        contents = Content.get_rendered_contents(qs)
        payload = self.make_payload(contents, "prepended")
        self.send(payload)

    def handle_load_more(self, data):
        """Load more content to the stream."""
        # TODO handle load according to stream qs - not public
        last_id = data.get("last_id")
        if not last_id:
            return
        qs = Content.objects.filter(id__lt=last_id)
        qs = Content.filter_for_user(qs, self.message.user).order_by("-created")[:10]
        contents = Content.get_rendered_contents(qs)
        payload = self.make_payload(contents, "appended")
        self.send(payload)

    @staticmethod
    def make_payload(contents, placement):
        payload = json.dumps({
            "event": "content",
            "contents": contents,
            "placement": placement,
        })
        return payload
