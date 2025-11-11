from drf_haystack.serializers import HaystackSerializer
from drf_haystack.viewsets import HaystackViewSet

from socialhome.content.utils import safe_text
from socialhome.content.search_indexes import TagIndex
from socialhome.users.search_indexes import ProfileIndex
from socialhome.search.utils import get_single_object

class ResultSerializer(HaystackSerializer):
    class Meta:
        index_classes = [ProfileIndex, TagIndex]
        fields = ['finger', 'name', 'avatar_url', 'uuid']


class SearchViewSet(HaystackViewSet):
    serializer_class = ResultSerializer

    def list(self, request, *args, **kwargs):
        q = safe_text(request.GET.get('name__startswith'))
        if q:
            q = q.strip().strip("@")

        resp = get_single_object(q, request, api=True, *args, **kwargs)
        if not resp: resp = super().list(request, *args, **kwargs)
        return resp

