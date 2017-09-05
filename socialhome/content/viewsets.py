from django.core.exceptions import ValidationError
from rest_framework import exceptions
from rest_framework import mixins
from rest_framework.decorators import detail_route
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.throttling import UserRateThrottle
from rest_framework.viewsets import GenericViewSet

from socialhome.content.models import Content
from socialhome.content.serializers import ContentSerializer


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

        if request.user.is_authenticated:
            if view.action == "share" or obj.author == request.user.profile:
                return True

        return False


class CreateContentThrottle(UserRateThrottle):
    scope = "content_create"


class ContentViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin, GenericViewSet):
    """
    create:
        Create content

        Required values: `text` and `visibility`.

        `visibility` should be one of: `public`, `site`, `limited`, `self`.

    share:
        Content sharing

        No additional required values. Create or remove a share of this content.

        Successful create share returns content ID as `content_id`.
    """
    queryset = Content.objects.none()
    serializer_class = ContentSerializer
    permission_classes = (IsOwnContentOrReadOnly,)
    throttle_classes = (CreateContentThrottle,)

    def _share(self):
        content = self.get_object()
        try:
            share = content.share(self.request.user.profile)
        except ValidationError as e:
            raise exceptions.ValidationError(e.message)
        except Exception:
            raise exceptions.APIException("Unknown error when creating share.")
        return Response({"status": "ok", "content_id": share.id}, status=HTTP_201_CREATED)

    def _unshare(self):
        content = self.get_object()
        try:
            content.unshare(self.request.user.profile)
        except ValidationError as e:
            raise exceptions.ValidationError(e.message)
        except Exception:
            raise exceptions.APIException("Unknown error when creating share.")
        return Response({"status": "ok"}, status=HTTP_204_NO_CONTENT)

    def get_queryset(self):
        if self.request.user.is_staff:
            return Content.objects.all()
        return Content.objects.visible_for_user(self.request.user)

    @detail_route(methods=["delete", "post"])
    def share(self, request, pk=None):
        if request.method == "POST":
            return self._share()
        elif request.method == "DELETE":
            return self._unshare()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user.profile)
