from haystack import indexes

from socialhome.enums import Visibility
from socialhome.users.models import Profile


class IntegerEnumField(indexes.IntegerField):
    def convert(self, value):
        """Override to get the number from the Enum, if we're passed an Enum."""
        if value is None:
            return None
        try:
            return value.value
        except AttributeError:
            return value


class ProfileIndex(indexes.ModelSearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)
    profile_visibility = IntegerEnumField(model_attr="visibility")

    class Meta:
        model = Profile
        fields = ("name", "handle")

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.exclude(visibility=Visibility.SELF)

    def should_update(self, instance, **kwargs):
        """Ensure we don't update SELF profiles to the index."""
        return instance.visibility != Visibility.SELF
