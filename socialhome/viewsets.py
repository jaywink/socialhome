from rest_framework.generics import CreateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle

from socialhome.serializers import ImageUploadSerializer, MediaUploadSerializer


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


class MediaUploadThrottle(UserRateThrottle):
    scope = "image_upload"


class MediaUploadView(CreateAPIView):
    """
    post:
        Upload a media file (image, audio or video)

        Return is JSON containing the ``url`` to the uploaded image NOTE! Uploading a media file doesn't post
        it out or create automatic content. Uploaded media files must be followed by a "content" create with
        the uploaded media files added to the content text.
    """
    serializer_class = MediaUploadSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)
    throttle_classes = (MediaUploadThrottle,)

    def perform_create(self, serializer):
        media = serializer.save(user=self.request.user)
