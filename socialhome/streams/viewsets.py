from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from socialhome.content.models import Tag
from socialhome.content.serializers import ContentSerializer
from socialhome.streams.streams import PublicStream, FollowedStream, TagStream, ProfileAllStream, ProfilePinnedStream
from socialhome.users.models import Profile


class StreamsAPIBaseView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.last_id = request.GET.get("last_id")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        qs, throughs = self.get_content()
        serializer = ContentSerializer(qs, many=True, context={"throughs": throughs})
        return Response(serializer.data)

    def get_content(self):
        raise NotImplemented


class FollowedStreamAPIView(StreamsAPIBaseView):
    permission_classes = (IsAuthenticated,)

    def get_content(self):
        stream = FollowedStream(last_id=self.last_id, user=self.request.user)
        return stream.get_content()


class ProfileAllStreamAPIView(StreamsAPIBaseView):
    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(Profile, id=kwargs.get("id"))
        return super().dispatch(request, *args, **kwargs)

    def get_content(self):
        stream = ProfileAllStream(last_id=self.last_id, profile=self.profile, user=self.request.user)
        return stream.get_content()


class ProfilePinnedStreamAPIView(StreamsAPIBaseView):
    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(Profile, id=kwargs.get("id"))
        return super().dispatch(request, *args, **kwargs)

    def get_content(self):
        stream = ProfilePinnedStream(last_id=self.last_id, profile=self.profile, user=self.request.user)
        return stream.get_content()


class PublicStreamAPIView(StreamsAPIBaseView):
    def get_content(self):
        stream = PublicStream(last_id=self.last_id)
        return stream.get_content()


class TagStreamAPIView(StreamsAPIBaseView):
    def dispatch(self, request, *args, **kwargs):
        self.tag = get_object_or_404(Tag, name=kwargs.get("name"))
        return super().dispatch(request, *args, **kwargs)

    def get_content(self):
        stream = TagStream(last_id=self.last_id, tag=self.tag, user=self.request.user)
        return stream.get_content()
