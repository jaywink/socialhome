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
        elif action == "load_children":
            self.handle_load_children(data)

    def _get_stream_qs(self):
        """Using the stream info, get correct queryset to use for content."""
        stream_info = self.kwargs.get("stream").split("__")
        if stream_info[0] == "public":
            return Content.objects.public()
        elif stream_info[0] == "tags":
            return Content.objects.tags(stream_info[1], self.message.user)
        elif stream_info[0] == "profile":
            return Content.objects.profile(stream_info[1], self.message.user)
        return Content.objects.none()

    def handle_load_content(self, data):
        """Send back the requested content."""
        ids = data.get("ids")
        if not ids:
            return
        qs = self._get_stream_qs()
        qs = qs.filter(id__in=ids)
        contents = Content.get_rendered_contents(qs)
        payload = self.make_payload(contents, "prepended")
        self.send_payload(payload)

    def handle_load_more(self, data):
        """Load more content to the stream."""
        last_id = data.get("last_id")
        if not last_id:
            return
        qs = self._get_stream_qs()
        qs = qs.filter(id__lt=last_id)[:20]
        contents = Content.get_rendered_contents(qs)
        payload = self.make_payload(contents, "appended")
        self.send_payload(payload)

    def handle_load_children(self, data):
        content_id = data.get("content_id")
        if not content_id:
            return
        # TODO: get recursively
        qs = Content.objects.children(content_id, self.message.user)
        contents = Content.get_rendered_contents(qs)
        payload = self.make_payload(contents, "children")
        payload["parent_id"] = content_id
        self.send_payload(payload)

    def send_payload(self, payload):
        self.send(json.dumps(payload))

    @staticmethod
    def make_payload(contents, placement):
        return {
            "event": "content",
            "contents": contents,
            "placement": placement,
        }
