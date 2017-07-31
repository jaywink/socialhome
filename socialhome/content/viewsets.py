from rest_framework.generics import CreateAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.viewsets import ModelViewSet

from socialhome.content.models import Content
from socialhome.content.serializers import ContentSerializer, ImageUploadSerializer


class IsOwnContentOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        if request.user.is_authenticated:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return request.user.is_authenticated and obj.author == request.user.profile


class CreateContentThrottle(UserRateThrottle):
    scope = "content_create"


class ContentViewSet(ModelViewSet):
    queryset = Content.objects.none()
    serializer_class = ContentSerializer
    permission_classes = (IsOwnContentOrReadOnly,)
    throttle_classes = (CreateContentThrottle,)

    def get_queryset(self):
        if self.request.user.is_staff:
            return Content.objects.all()
        return Content.objects.visible_for_user(self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user.profile)


class ImageUploadThrottle(UserRateThrottle):
    scope = "image_upload"


class ImageUploadView(CreateAPIView):
    serializer_class = ImageUploadSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)
    throttle_classes = (ImageUploadThrottle,)
