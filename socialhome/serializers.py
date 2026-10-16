from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer

from socialhome.models import MediaUpload
from socialhome.users.models import User


class MediaUploadSerializer(ModelSerializer):
    class Meta:
        model = MediaUpload
        fields = ['category', 'media']

    def validate_media(self, value):
        if value:
            return value
        raise ValidationError("Invalid media")

    def validate_category(self, value):
        if value in ('uploads', 'avatars', 'pictures'): return value
        raise ValidationError("Invalid media category")
