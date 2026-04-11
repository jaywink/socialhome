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

    def create(self, data):
        self.is_valid(raise_exception=True)

        obj = MediaUpload.objects.create(**data)

        # Ensure the Profile.image_url_{small,medium,large} properties are updated
        # Outbound Diaspora payloads and the old UI require this
        if obj.category == "avatars":
            user = self.context.get("request").user
            user.picture.name = obj.media.name
            User.objects.filter(id=user.id).update(picture=user.picture)
            user.copy_picture_to_profile(save=False)

        return obj

