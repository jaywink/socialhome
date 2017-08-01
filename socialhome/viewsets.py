from rest_framework.generics import CreateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle

from socialhome.serializers import ImageUploadSerializer


class ImageUploadThrottle(UserRateThrottle):
    scope = "image_upload"


class ImageUploadView(CreateAPIView):
    serializer_class = ImageUploadSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)
    throttle_classes = (ImageUploadThrottle,)
