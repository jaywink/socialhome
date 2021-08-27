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
    def dispatch(self, request, *args, **kwargs):
        self.last_id = request.GET.get("last_id")
        self.accept_ids = request.GET.get("accept_ids", None)
        if self.accept_ids:
            self.accept_ids = self.accept_ids.split(",")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        qs, throughs = self.get_content()
        serializer = ContentSerializer(qs, many=True, context={"throughs": throughs, "request": request})
        return Response(serializer.data)

    def get_content(self):
        return [], {}


class FollowedStreamAPIView(StreamsAPIBaseView):
    permission_classes = (IsAuthenticated,)

    def get_content(self):
        stream = FollowedStream(last_id=self.last_id, user=self.request.user, accept_ids=self.accept_ids)
        return stream.get_content()


class LimitedStreamAPIView(StreamsAPIBaseView):
    permission_classes = (IsAuthenticated,)

    def get_content(self):
        stream = LimitedStream(last_id=self.last_id, user=self.request.user, accept_ids=self.accept_ids)
        return stream.get_content()


class LocalStreamAPIView(StreamsAPIBaseView):
    def get_content(self):
        stream = LocalStream(last_id=self.last_id, user=self.request.user, accept_ids=self.accept_ids)
        return stream.get_content()


class ProfileAllStreamAPIView(StreamsAPIBaseView):
    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(Profile, uuid=kwargs.get("uuid"))
        return super().dispatch(request, *args, **kwargs)

    def get_content(self):
        stream = ProfileAllStream(
            last_id=self.last_id, profile=self.profile, user=self.request.user, accept_ids=self.accept_ids,
        )
        return stream.get_content()


class ProfilePinnedStreamAPIView(StreamsAPIBaseView):
    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(Profile, uuid=kwargs.get("uuid"))
        return super().dispatch(request, *args, **kwargs)

    def get_content(self):
        stream = ProfilePinnedStream(
            last_id=self.last_id, profile=self.profile, user=self.request.user, accept_ids=self.accept_ids,
        )
        return stream.get_content()


class PublicStreamAPIView(StreamsAPIBaseView):
    def get_content(self):
        stream = PublicStream(last_id=self.last_id, accept_ids=self.accept_ids)
        return stream.get_content()


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
        stream = TagStream(last_id=self.last_id, tag=self.tag, user=self.request.user, accept_ids=self.accept_ids)
        return stream.get_content()


class TagsStreamAPIView(StreamsAPIBaseView):
    permission_classes = (IsAuthenticated,)

    def get_content(self):
        stream = TagsStream(last_id=self.last_id, user=self.request.user, accept_ids=self.accept_ids)
        return stream.get_content()
