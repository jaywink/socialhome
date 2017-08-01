from rest_framework.generics import CreateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle

from socialhome.serializers import ImageUploadSerializer


class ImageUploadThrottle(UserRateThrottle):
    scope = "image_upload"


class ImageUploadView(CreateAPIView):
    """
    post:
        Upload an image

        Return is JSON containing the ``url`` to the uploaded image and the markdown ``code`` to
        embed the image in content. NOTE! Uploading an image doesn't post it out or create automatic content.
        Uploaded images must be followed by a "content" create with the uploaded images added to the content text.
    """
    serializer_class = ImageUploadSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)
    throttle_classes = (ImageUploadThrottle,)
