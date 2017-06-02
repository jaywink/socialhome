from rest_framework.decorators import detail_route
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from socialhome.users.models import User, Profile
from socialhome.users.serializers import UserSerializer


class IsSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user


class UserViewSet(ReadOnlyModelViewSet):
    queryset = User.objects.none()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @detail_route(methods=["post"], permission_classes=[IsAuthenticated, IsSelf])
    def add_follower(self, request, pk=None):
        guid = request.data.get("guid")
        try:
            profile = Profile.objects.visible_for_user(request.user).get(guid=guid)
        except Profile.DoesNotExist:
            raise PermissionDenied("Profile given either does not exist or is not visible.")
        user = self.get_object()
        if user.profile.guid == guid:
            raise ValidationError("Cannot follow self!")
        user.following.add(profile)
        return Response({"status": "Follower added."})

    @detail_route(methods=["post"], permission_classes=[IsAuthenticated, IsSelf])
    def remove_follower(self, request, pk=None):
        guid = request.data.get("guid")
        try:
            profile = Profile.objects.get(guid=guid)
        except Profile.DoesNotExist:
            raise PermissionDenied("Profile given does not exist.")
        user = self.get_object()
        if user.profile.guid == guid:
            raise ValidationError("Cannot unfollow self!")
        user.following.remove(profile)
        return Response({"status": "Follower removed."})
