from haystack import indexes

from socialhome.content.models import Tag

class TagIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    name = indexes.CharField(model_attr="name")
    uuid = indexes.CharField(model_attr="uuid", indexed=False)

    def get_model(self):
        return Tag

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_name(self, obj):
        if len(obj.name.encode("utf8")) > 245:
            # Xapian wont allow documents longer than this, see
            # https://getting-started-with-xapian.readthedocs.io/en/latest/concepts/indexing/limitations.html
            # We could do something smarter here, but for now just skip the tag.
            return None
        return obj.name
