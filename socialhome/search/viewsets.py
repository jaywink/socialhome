from haystack.query import SearchQuerySet
from rest_framework.mixins import ListModelMixin
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.viewsets import GenericViewSet

from socialhome.content.utils import safe_text
from socialhome.content.search_indexes import TagIndex
from socialhome.users.search_indexes import ProfileIndex
from socialhome.search.utils import get_single_object


class SearchSerializer(BaseSerializer):
    def to_representation(self, instance):
        return {
            "finger": instance.finger,
            "name": instance.name,
            "avatar_url": instance.avatar_url,
            "uuid": instance.uuid
        }


class SearchAPIViewSet(ListModelMixin, GenericViewSet):
    serializer_class = SearchSerializer

    def list(self, request, *args, **kwargs):
        q = safe_text(request.GET.get('name__startswith'))
        if q:
            q = q.strip().strip("@")

        resp = get_single_object(q, request, api=True)
        if not resp:
            self.queryset = SearchQuerySet().filter(name__startswith=q) if q else SearchQuerySet().none()
            resp = super().list(request, *args, **kwargs)
        return resp

