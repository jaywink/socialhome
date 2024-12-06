from django.conf import settings
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ImageField, SerializerMethodField
from rest_framework.serializers import ModelSerializer, Serializer

from socialhome.forms import MarkdownXImageForm
from socialhome.models import MediaUpload


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

       return MediaUpload.objects.create(user=self.context.get("request").user, **data)

