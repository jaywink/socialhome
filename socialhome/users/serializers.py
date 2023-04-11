from typing import List

from enumfields.drf import EnumField
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from socialhome.content.models import Content
from socialhome.enums import Visibility
from socialhome.users.models import User, Profile

class LimitedProfileSerializer(ModelSerializer):
    """Read only Profile serializer with less information.

    For example for adding to serialized Content.
    """
    user_following = SerializerMethodField()

    class Meta:
        model = Profile
        fields = (
            "fid",
            "uuid",
            "handle",
            "home_url",
            "finger",
            "id",
            "image_url_small",
            "image_url_medium",
            "image_url_large",
            "is_local",
            "name",
            "url",
            "user_following",
        )
        read_only_fields = (
            "fid",
            "uuid",
            "handle",
            "home_url",
            "finger",
            "id",
            "image_url_small",
            "image_url_medium",
            "image_url_large",
            "is_local",
            "name",
            "url",
            "user_following",
        )

    def get_user_following(self, obj: Profile) -> bool:
        request = self.context.get("request")
        if not request:
            return False
        return bool(request.user.is_authenticated and obj.id in request.user.profile.following_ids)


class ProfileSerializer(ModelSerializer):
    followed_tags = SerializerMethodField()
    followers_count = SerializerMethodField()
    following_count = SerializerMethodField()
    has_pinned_content = SerializerMethodField()
    user_following = SerializerMethodField()
    visibility = EnumField(Visibility, lenient=True, ints_as_names=True)

    class Meta:
        model = Profile
        fields = (
            "fid",
            "followed_tags",
            "followers_count",
            "following_count",
            "uuid",
            "finger",
            "handle",
            "has_pinned_content",
            "home_url",
            "id",
            "image_url_large",
            "image_url_medium",
            "image_url_small",
            "is_local",
            "location",
            "name",
            "nsfw",
            "url",
            "user_following",
            "visibility",
        )
        read_only_fields = (
            "fid",
            "followed_tags",
            "followers_count",
            "following_count",
            "uuid",
            "finger",
            "handle",
            "has_pinned_content",
            "home_url",
            "id",
            "image_url_large",
            "image_url_medium",
            "image_url_small",
            "is_local",
            "url",
            "user_following",
        )

    def get_followed_tags(self, obj: Profile) -> List:
        """
        Return list of followed tags if owned by logged in user.
        """
        user = self.context.get("request").user
        if (hasattr(user, "profile") and user.profile.id == obj.id) or user.is_staff:
            return list(obj.followed_tags.values_list('name', flat=True))
        return []

    def get_following_count(self, obj):
        return obj.following.count()

    def get_followers_count(self, obj):
        return Profile.objects.followers(obj).count()

    def get_has_pinned_content(self, obj):
        user = self.context.get("request").user
        return Content.objects.profile_pinned(obj, user).exists()

    def get_user_following(self, obj):
        request = self.context.get("request")
        if not request:
            return False
        return bool(request.user.is_authenticated and obj.id in request.user.profile.following_ids)


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "name", "username", "email")
