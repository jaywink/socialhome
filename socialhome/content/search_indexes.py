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
