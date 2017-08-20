from enumfields.drf import EnumField
from rest_framework.serializers import ModelSerializer

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.enums import Visibility


class ContentSerializer(ModelSerializer):
    visibility = EnumField(Visibility, lenient=True, ints_as_names=True)
    content_type = EnumField(ContentType, ints_as_names=True, read_only=True)

    class Meta:
        model = Content
        fields = ("id", "text", "rendered", "guid", "author", "pinned", "order", "service_label", "oembed",
                  "opengraph", "tags", "parent", "remote_created", "created", "modified", "visibility",
                  "content_type")
        read_only_fields = ("id", "rendered", "guid", "author", "oembed", "opengraph", "tags", "parent",
                            "remote_created", "created", "modified", "content_type")
