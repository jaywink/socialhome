from haystack import indexes

from socialhome.enums import Visibility
from socialhome.users.models import Profile


class ProfileIndex(indexes.ModelSearchIndex, indexes.Indexable):
    class Meta:
        model = Profile
        fields = ("name", "handle")

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.exclude(visibility=Visibility.SELF)
