from enumfields.drf import EnumField
from rest_framework.serializers import ModelSerializer

from socialhome.enums import Visibility
from socialhome.users.models import User, Profile


class ProfileSerializer(ModelSerializer):
    visibility = EnumField(Visibility, lenient=True, ints_as_names=True)

    class Meta:
        model = Profile
        fields = (
            "guid",
            "handle",
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
            "visibility",
        )
        read_only_fields = (
            "guid",
            "handle",
            "home_url",
            "id",
            "image_url_large",
            "image_url_medium",
            "image_url_small",
            "is_local",
            "url",
        )


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "name", "username", "email")
