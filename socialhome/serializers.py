from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ImageField
from rest_framework.serializers import ModelSerializer, Serializer

from socialhome.forms import MarkdownXImageForm
from socialhome.models import MediaUpload
from socialhome.users.models import User


class ImageUploadSerializer(Serializer):
    image = ImageField()

    def validate_image(self, value):
        self.form = MarkdownXImageForm(files={"image": value}, user=self.context.get("request").user)
        if self.form.is_valid():
            return value
        raise ValidationError("Invalid image")

    def create(self, data):
        image_path = self.form.save(commit=True)
        image_url = "%s%s" % (settings.SOCIALHOME_URL, image_path)
        image_code = '![]({})'.format(image_url)
        return {
            "code": image_code,
            "url": image_url,
        }

    def to_representation(self, instance):
        return instance


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

