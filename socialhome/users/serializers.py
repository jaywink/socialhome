from rest_framework.serializers import ModelSerializer

from socialhome.users.models import User, Profile


class ProfileSerializer(ModelSerializer):
    class Meta:
        model = Profile
        fields = ("id", "name", "user", "guid", "handle", "rsa_public_key", "image_url_large",
                  "image_url_medium", "image_url_small", "location", "nsfw")
        read_only_fields = ("id", "user", "guid", "handle", "rsa_public_key", "image_url_large",
                            "image_url_medium", "image_url_small")


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "name", "username", "email")
