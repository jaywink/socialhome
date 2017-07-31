from django.conf import settings
from enumfields.drf import EnumField
from markdownx.forms import ImageForm
from rest_framework.exceptions import ValidationError
from rest_framework.fields import ImageField
from rest_framework.serializers import ModelSerializer, Serializer

from socialhome.content.models import Content
from socialhome.enums import Visibility


class ContentSerializer(ModelSerializer):
    visibility = EnumField(Visibility, lenient=True)

    class Meta:
        model = Content
        fields = ("id", "text", "rendered", "guid", "author", "pinned", "order", "service_label", "oembed",
                  "opengraph", "tags", "parent", "remote_created", "created", "modified", "visibility")
        read_only_fields = ("id", "rendered", "guid", "author", "oembed", "opengraph", "tags", "parent",
                            "remote_created", "created", "modified")


class ImageUploadSerializer(Serializer):
    image = ImageField()

    def validate_image(self, value):
        self.form = ImageForm(files={"image": value})
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
