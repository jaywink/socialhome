from django.db.models import Count
from haystack import indexes

from socialhome.content.models import Tag


class TagIndex(indexes.ModelSearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    class Meta:
        model = Tag
        fields = ("name",)

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.annotate(content_count=Count('contents')).filter(content_count__gt=0)
