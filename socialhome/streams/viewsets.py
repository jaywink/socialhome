from django.conf import settings
from django.http import Http404
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from socialhome.content.models import Tag
from socialhome.content.serializers import ContentSerializer
from socialhome.streams.streams import (
    PublicStream, FollowedStream, TagStream, ProfileAllStream, ProfilePinnedStream, LimitedStream, LocalStream,
    TagsStream)
from socialhome.users.models import Profile


class StreamsAPIBaseView(APIView):
    stream = None

    def dispatch(self, request, *args, **kwargs):
        self.last_id = request.GET.get("last_id")
        self.accept_ids = request.GET.get("accept_ids", None)
        if self.accept_ids:
            self.accept_ids = self.accept_ids.split(",")
        self.newest_through_id = request.GET.get("newest_through_id")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        qs, throughs = self.get_content()
        serializer = ContentSerializer(qs, many=True, context={"throughs": throughs, "request": request})
        data = serializer.data
        # Hack used to send the ws channel name the SPA UI
        if request.version == '2.0':
            data = {"notify_key": self.stream.notify_key,
                    "unfetched_content": self.stream.unfetched_content,
                    "data": data}
        return Response(data)

    def get_content(self):
        return [], {}


class FollowedStreamAPIView(StreamsAPIBaseView):
    permission_classes = (IsAuthenticated,)

    def get_content(self):
        self.stream = FollowedStream(last_id=self.last_id, newest_through_id=self.newest_through_id, user=self.request.user, accept_ids=self.accept_ids)
        return self.stream.get_content()


class LimitedStreamAPIView(StreamsAPIBaseView):
    permission_classes = (IsAuthenticated,)

    def get_content(self):
        self.stream = LimitedStream(last_id=self.last_id, newest_through_id=self.newest_through_id, user=self.request.user, accept_ids=self.accept_ids)
        return self.stream.get_content()


class LocalStreamAPIView(StreamsAPIBaseView):
    def get_content(self):
        self.stream = LocalStream(last_id=self.last_id, newest_through_id=self.newest_through_id, user=self.request.user, accept_ids=self.accept_ids)
        return self.stream.get_content()


class ProfileAllStreamAPIView(StreamsAPIBaseView):
    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(Profile, uuid=kwargs.get("uuid"))
        return super().dispatch(request, *args, **kwargs)

    def get_content(self):
        self.stream = ProfileAllStream(
            last_id=self.last_id, newest_through_id=self.newest_through_id, profile=self.profile, user=self.request.user, accept_ids=self.accept_ids,
        )
        return self.stream.get_content()


class ProfilePinnedStreamAPIView(StreamsAPIBaseView):
    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(Profile, uuid=kwargs.get("uuid"))
        return super().dispatch(request, *args, **kwargs)

    def get_content(self):
        self.stream = ProfilePinnedStream(
            last_id=self.last_id, newest_through_id=self.newest_through_id, profile=self.profile, user=self.request.user, accept_ids=self.accept_ids,
        )
        return self.stream.get_content()


class PublicStreamAPIView(StreamsAPIBaseView):
    def dispatch(self, request, *args, **kwargs):
        # must be called first to ensure token authentication is processed
        response = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated and not settings.SOCIALHOME_STREAMS_PUBLIC_STREAM_WITHOUT_AUTH:
            raise Http404
        return response

    def get_content(self):
        self.stream = PublicStream(last_id=self.last_id, newest_through_id=self.newest_through_id, accept_ids=self.accept_ids, user=self.request.user)
        return self.stream.get_content()


class TagStreamAPIView(StreamsAPIBaseView):
    def dispatch(self, request, *args, **kwargs):
        if kwargs.get("name"):
            arguments = {"name": kwargs.get("name")}
        elif kwargs.get("uuid"):
            arguments = {"uuid": kwargs.get("uuid")}
        else:
            raise Http404
        self.tag = get_object_or_404(Tag, **arguments)
        return super().dispatch(request, *args, **kwargs)

    def get_content(self):
        self.stream = TagStream(last_id=self.last_id, newest_through_id=self.newest_through_id, tag=self.tag, user=self.request.user, accept_ids=self.accept_ids)
        return self.stream.get_content()


class TagsStreamAPIView(StreamsAPIBaseView):
    permission_classes = (IsAuthenticated,)

    def get_content(self):
        self.stream = TagsStream(last_id=self.last_id, newest_through_id=self.newest_through_id, user=self.request.user, accept_ids=self.accept_ids)
        return self.stream.get_content()
