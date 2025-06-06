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
    avatar_url = indexes.CharField(model_attr="avatar_url", indexed=False, null=True)
    uuid = indexes.CharField(model_attr="uuid", indexed=False)
    profile_visibility = IntegerEnumField(model_attr="visibility")

    class Meta:
        model = Profile
        fields = ("name", "finger", "avatar_url", "uuid")

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.exclude(visibility=Visibility.SELF)

    def prepare_finger(self, obj):
        if not obj.finger:
            return None
        if len(obj.finger.encode("utf8")) > 245:
            # Xapian wont allow documents longer than this, see
            # https://getting-started-with-xapian.readthedocs.io/en/latest/concepts/indexing/limitations.html
            # We could do something smarter here, but for now just skip the tag.
            return None
        return obj.finger

    def prepare_name(self, obj):
        if not obj.name:
            return None
        if len(obj.name.encode("utf8")) > 245:
            # Xapian wont allow documents longer than this, see
            # https://getting-started-with-xapian.readthedocs.io/en/latest/concepts/indexing/limitations.html
            # We could do something smarter here, but for now just skip the tag.
            return None
        return obj.name

    def should_update(self, instance, **kwargs):
        """Ensure we don't update SELF profiles to the index."""
        return instance.visibility != Visibility.SELF
