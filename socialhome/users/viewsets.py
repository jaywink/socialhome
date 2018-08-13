import django_rq
from django.http import HttpResponse
from rest_framework import mixins, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from socialhome.enums import Visibility
from socialhome.users.models import User, Profile
from socialhome.users.serializers import UserSerializer, ProfileSerializer
from socialhome.users.tasks.exports import create_user_export, UserExporter


class IsOwnProfileOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        if not request.user.is_authenticated:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return obj.user == request.user


class ProfileViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, GenericViewSet):
    queryset = Profile.objects.none()
    serializer_class = ProfileSerializer
    permission_classes = (IsOwnProfileOrReadOnly,)

    def get_queryset(self):
        qs = Profile.objects.visible_for_user(self.request.user)
        if self.action == "list" and not self.request.user.is_staff:
            # Filter out also LIMITED profiles since those don't want to be "searched"
            qs = qs.exclude(visibility=Visibility.LIMITED)
        return qs

    @detail_route(methods=["post"])
    def add_follower(self, request, pk=None):
        uuid = request.data.get("uuid")
        try:
            target_profile = Profile.objects.get(uuid=uuid)
        except Profile.DoesNotExist:
            raise PermissionDenied("Profile given does not exist.")
        profile = self.get_object()
        if profile.uuid == uuid:
            raise ValidationError("Cannot follow self!")
        profile.following.add(target_profile)
        return Response({"status": "Follower added."})

    @list_route(methods=["post"], permission_classes=(IsAuthenticated,))
    def create_export(self, request, pk=None):
        django_rq.enqueue(create_user_export, request.user.id)
        return Response({"status": "Data export job queued."})

    @detail_route(methods=["post"])
    def remove_follower(self, request, pk=None):
        uuid = request.data.get("uuid")
        try:
            target_profile = Profile.objects.get(uuid=uuid)
        except Profile.DoesNotExist:
            raise PermissionDenied("Profile given does not exist.")
        profile = self.get_object()
        if profile.uuid == uuid:
            raise ValidationError("Cannot unfollow self!")
        profile.following.remove(target_profile)
        return Response({"status": "Follower removed."})

    @list_route(methods=["get"], permission_classes=(IsAuthenticated,))
    def retrieve_export(self, request, pk=None):
        exporter = UserExporter(request.user)
        zipf = exporter.retrieve()
        if not zipf:
            return Response({"status": "No export available"}, status=status.HTTP_400_BAD_REQUEST)
        response = HttpResponse(zipf, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=%s' % exporter.name
        return response


class UserViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    queryset = User.objects.none()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
