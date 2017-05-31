from rest_framework.serializers import ModelSerializer

from socialhome.users.models import User


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "name", "followers", "following", "username", "email")
