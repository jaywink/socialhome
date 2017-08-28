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
        fields = (
            "author",
            "content_type",
            "created",
            "guid",
            "id",
            "local",
            "modified",
            "oembed",
            "opengraph",
            "order",
            "parent",
            "pinned",
            "remote_created",
            "rendered",
            "reply_count",
            "service_label",
            "shares_count",
            "tags",
            "text",
            "visibility",
        )
        read_only_fields = (
            "author",
            "content_type"
            "created",
            "guid",
            "id",
            "local",
            "modified",
            "oembed",
            "opengraph",
            "parent",
            "remote_created",
            "rendered",
            "reply_count",
            "shares_count",
            "tags",
        )
