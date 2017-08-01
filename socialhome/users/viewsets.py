from rest_framework import mixins
from rest_framework.decorators import detail_route
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, GenericViewSet

from socialhome.enums import Visibility
from socialhome.users.models import User, Profile
from socialhome.users.serializers import UserSerializer, ProfileSerializer


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


class ProfileViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin, GenericViewSet):
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
        guid = request.data.get("guid")
        try:
            target_profile = Profile.objects.get(guid=guid)
        except Profile.DoesNotExist:
            raise PermissionDenied("Profile given does not exist.")
        profile = self.get_object()
        if profile.guid == guid:
            raise ValidationError("Cannot follow self!")
        profile.following.add(target_profile)
        return Response({"status": "Follower added."})

    @detail_route(methods=["post"])
    def remove_follower(self, request, pk=None):
        guid = request.data.get("guid")
        try:
            target_profile = Profile.objects.get(guid=guid)
        except Profile.DoesNotExist:
            raise PermissionDenied("Profile given does not exist.")
        profile = self.get_object()
        if profile.guid == guid:
            raise ValidationError("Cannot unfollow self!")
        profile.following.remove(target_profile)
        return Response({"status": "Follower removed."})


class UserViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.none()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
