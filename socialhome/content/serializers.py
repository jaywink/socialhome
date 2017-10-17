from enumfields.drf import EnumField
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer, SlugRelatedField

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.enums import Visibility
from socialhome.users.serializers import LimitedProfileSerializer


class ContentSerializer(ModelSerializer):
    author = LimitedProfileSerializer(read_only=True)
    content_type = EnumField(ContentType, ints_as_names=True, read_only=True)
    user_following_author = SerializerMethodField()
    user_is_author = SerializerMethodField()
    user_has_shared = SerializerMethodField()
    tags = SlugRelatedField(many=True, read_only=True, slug_field="name")
    through = SerializerMethodField()
    visibility = EnumField(Visibility, lenient=True, ints_as_names=True)

    class Meta:
        model = Content
        fields = (
            "author",
            "content_type",
            "edited",
            "guid",
            "humanized_timestamp",
            "id",
            "is_nsfw",
            "local",
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
            "through",
            "timestamp",
            "url",
            "user_following_author",
            "user_is_author",
            "user_has_shared",
            "visibility",
        )
        read_only_fields = (
            "author",
            "content_type"
            "edited",
            "guid",
            "humanized_timestamp",
            "id",
            "is_nsfw",
            "local",
            "parent",
            "remote_created",
            "rendered",
            "reply_count",
            "shares_count",
            "tags",
            "through",
            "timestamp",
            "url",
            "user_following_author",
            "user_is_author",
            "user_has_shared",
        )

    def get_through(self, obj):
        """Through is generally required only for serializing content for streams."""
        throughs = self.context.get("throughs")
        if not throughs:
            return obj.id
        return throughs.get(obj.id, obj.id)

    def get_user_following_author(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        return bool(request.user.is_authenticated and obj.author_id in request.user.profile.following_ids)

    def get_user_is_author(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        return bool(request.user.is_authenticated and obj.author == request.user.profile)

    def get_user_has_shared(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        return Content.has_shared(obj.id, request.user.profile.id) if hasattr(request.user, "profile") else False
