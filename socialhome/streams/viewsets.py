from django.conf import settings
from django.http import Http404
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from socialhome.content.models import Tag
from socialhome.content.serializers import ContentSerializer
from socialhome.streams.enums import StreamType
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
        self.first_id = request.GET.get("first_id")
        self.unfetched_count = request.GET.get("unfetched_count", False)
        if self.unfetched_count == '': self.unfetched_count = True
        self.set_stream()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        if request.version == '2.0' and self.unfetched_count:
            data = {'count': self.get_content_count()}
            return Response(data)
        else:
            qs, throughs = self.get_content()
            serializer = ContentSerializer(qs, many=True, context={"throughs": throughs, "request": request})
            data = serializer.data
        # Hack used to send the ws channel name and relevant context data to the SPA UI
        # This is used in lieu of json context
        if request.version == '2.0':
            data = {"context": self.stream.get_context_data(),
                    "data": data}
        return Response(data)

    def get_content(self):
        return self.stream.get_content()

    def get_content_count(self):
        paginate_by = self.stream.paginate_by
        self.stream.paginate_by = 500
        ids, _ = self.stream.get_content_ids()
        self.stream.paginate_by = paginate_by
        return len(ids)
    
    def set_stream(self):
        return [], {}


class FollowedStreamAPIView(StreamsAPIBaseView):
    permission_classes = (IsAuthenticated,)

    def set_stream(self):
        self.stream = FollowedStream(last_id=self.last_id, first_id=self.first_id, user=self.request.user, accept_ids=self.accept_ids)


class LimitedStreamAPIView(StreamsAPIBaseView):
    permission_classes = (IsAuthenticated,)

    def set_stream(self):
        self.stream = LimitedStream(last_id=self.last_id, first_id=self.first_id, user=self.request.user, accept_ids=self.accept_ids)


class LocalStreamAPIView(StreamsAPIBaseView):
    def set_stream(self):
        self.stream = LocalStream(last_id=self.last_id, first_id=self.first_id, user=self.request.user, accept_ids=self.accept_ids)


class ProfileAllStreamAPIView(StreamsAPIBaseView):
    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(Profile, uuid=kwargs.get("uuid"))
        return super().dispatch(request, *args, **kwargs)

    def set_stream(self):
        self.stream = ProfileAllStream(
            last_id=self.last_id, first_id=self.first_id, profile=self.profile, user=self.request.user, accept_ids=self.accept_ids,
        )


class ProfilePinnedStreamAPIView(StreamsAPIBaseView):
    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(Profile, uuid=kwargs.get("uuid"))
        return super().dispatch(request, *args, **kwargs)

    def set_stream(self):
        self.stream = ProfilePinnedStream(
            last_id=self.last_id, first_id=self.first_id, profile=self.profile, user=self.request.user, accept_ids=self.accept_ids,
        )


class PublicStreamAPIView(StreamsAPIBaseView):
    def dispatch(self, request, *args, **kwargs):
        # must be called first to ensure token authentication is processed
        response = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated and not settings.SOCIALHOME_STREAMS_PUBLIC_STREAM_WITHOUT_AUTH:
            raise Http404
        return response

    def set_stream(self):
        self.stream = PublicStream(last_id=self.last_id, first_id=self.first_id, accept_ids=self.accept_ids, user=self.request.user)


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

    def set_stream(self):
        self.stream = TagStream(last_id=self.last_id, first_id=self.first_id, tag=self.tag, user=self.request.user, accept_ids=self.accept_ids)


class TagsStreamAPIView(StreamsAPIBaseView):
    permission_classes = (IsAuthenticated,)

    def set_stream(self):
        self.stream = TagsStream(last_id=self.last_id, first_id=self.first_id, user=self.request.user, accept_ids=self.accept_ids)
