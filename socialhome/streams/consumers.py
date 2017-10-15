import json

from channels.generic.websockets import WebsocketConsumer

from socialhome.content.models import Content, Tag
from socialhome.streams.streams import PublicStream, FollowedStream, TagStream


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

    def _get_base_qs(self):
        stream = self._get_stream_instance()
        if stream:
            return stream.get_queryset()
        stream_name, stream_info = self._get_stream_info()
        # TODO implement profile streams here too once done
        if stream_name == "profile":
            return Content.objects.profile_pinned(stream_info, self.message.user)
        elif stream_name == "profile_all":
            return Content.objects.profile_by_attr("id", stream_info, self.message.user)
        return Content.objects.none()

    def _get_stream_class(self):
        stream_name, _stream_info = self._get_stream_info()
        return {
            "public": PublicStream,
            "followed": FollowedStream,
            "tag": TagStream,
        }.get(stream_name)

    def _get_stream_info(self):
        """Take two first elements of the stream info split as stream name and info."""
        split = self.kwargs.get("stream").split("__")
        if len(split) < 2:
            return split[0], None
        return split[0], split[1]

    def _get_stream_instance(self, last_id=None):
        stream_cls = self._get_stream_class()
        if not stream_cls:
            return
        stream_name, stream_info = self._get_stream_info()
        if stream_name == "public":
            return self._get_stream_class()(last_id=last_id)
        elif stream_name == "followed":
            return self._get_stream_class()(last_id=last_id, user=self.message.user)
        elif stream_name == "tag":
            tag_id = stream_info.split("_")[0]
            tag = Tag.objects.get(id=tag_id)
            return self._get_stream_class()(last_id=last_id, user=self.message.user, tag=tag)

    def _get_stream_qs(self, last_id=None):
        """Using the stream info, get correct queryset to use for content.

        :returns: tuple of (QuerySet, list). The list is a list of "throughs" id's for the ordered content qs.
        """
        stream = self._get_stream_instance(last_id=last_id)
        if stream:
            return stream.get_content()
        stream_name, stream_info = self._get_stream_info()
        # TODO implement profile streams here too once done
        qs = None
        if stream_name == "profile":
            qs = Content.objects.profile_pinned(stream_info, self.message.user)
        elif stream_name == "profile_all":
            qs = Content.objects.profile_by_attr("id", stream_info, self.message.user)
        if qs:
            qs = qs.filter(id__lt=last_id)[:15]
            ids = qs.values_list("id", flat=True)
            throughs = zip(ids, ids)
            return qs, throughs
        return Content.objects.none(), None

    def handle_load_content(self, data):
        """Send back the requested content."""
        ids = data.get("ids")
        if not ids:
            return
        qs = self._get_base_qs()
        qs = qs.filter(id__in=ids)
        contents = Content.get_rendered_contents(qs, self.message.user)
        payload = self.make_payload(contents, "prepended")
        self.send_payload(payload)

    def handle_load_more(self, data):
        """Load more content to the stream."""
        last_id = data.get("last_id")
        if not last_id:
            return
        qs, throughs = self._get_stream_qs(last_id=last_id)
        contents = Content.get_rendered_contents(qs, self.message.user, throughs=throughs)
        payload = self.make_payload(contents, "appended")
        self.send_payload(payload)

    def handle_load_children(self, data):
        content_id = data.get("content_id")
        if not content_id:
            return
        # TODO: get recursively
        qs = Content.objects.children(content_id, self.message.user)
        contents = Content.get_rendered_contents(qs, self.message.user)
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
