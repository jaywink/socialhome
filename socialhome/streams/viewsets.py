from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from socialhome.content.models import Tag
from socialhome.content.serializers import ContentSerializer
from socialhome.streams.streams import PublicStream, FollowedStream, TagStream


class StreamsAPIBaseView(APIView):
    def dispatch(self, request, *args, **kwargs):
        self.last_id = request.GET.get("last_id")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        content = self.get_content()
        serializer = ContentSerializer(content, many=True)
        return Response(serializer.data)

    def get_content(self):
        raise NotImplemented


class FollowedStreamAPIView(StreamsAPIBaseView):
    permission_classes = (IsAuthenticated,)

    def get_content(self):
        stream = FollowedStream(last_id=self.last_id, user=self.request.user)
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
