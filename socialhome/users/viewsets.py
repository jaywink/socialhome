from typing import Any

import django_rq
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS, IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from socialhome.enums import Visibility
from socialhome.content.models import Content
from socialhome.users.models import User, Profile
from socialhome.users.serializers import UserSerializer, ProfileSerializer, LimitedProfileSerializer
from socialhome.users.tasks.exports import create_user_export, UserExporter
from socialhome.users.utils import get_recently_active_user_ids, update_profile


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
    lookup_field = 'uuid'

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.pagination_class.page_size_query_param = "page_size"

    def get_queryset(self):
        if self.action == 'organize':
            profile = get_object_or_404(Profile, user=self.request.user)
            return Content.objects.profile_pinned(profile, self.request.user).order_by("order")
        else:
            qs = Profile.objects.visible_for_user(self.request.user)
            if self.action == "list" and not self.request.user.is_staff:
                # Filter out also LIMITED profiles since those don't want to be "searched"
                qs = qs.exclude(visibility=Visibility.LIMITED)
            return qs

    @action(detail=True, methods=["post"])
    def follow(self, request, uuid=None):
        try:
            target_profile = Profile.objects.get(uuid=uuid)
        except Profile.DoesNotExist:
            raise PermissionDenied("Profile given does not exist.")
        profile = request.user.profile
        if str(profile.uuid) == uuid:
            raise ValidationError("Cannot follow self!")
        profile.following.add(target_profile)
        return Response({"status": "Followed."})

    @action(methods=["get"], detail=False, permission_classes=(IsAuthenticated,))
    def following(self, request):
        query_set = self.paginate_queryset(request.user.profile.following.all())
        values = [LimitedProfileSerializer(x, context={'request': request}).data for x in query_set]
        return self.get_paginated_response(values)

    @action(methods=["get"], detail=False, permission_classes=(IsAuthenticated,))
    def followers(self, request):
        query_set = self.paginate_queryset(request.user.profile.followers.all())
        values = [LimitedProfileSerializer(x, context={'request': request}).data for x in query_set]
        return self.get_paginated_response(values)

    @action(detail=False, methods=["post"], permission_classes=(IsAuthenticated,))
    def create_export(self, request, pk=None):
        django_rq.enqueue(create_user_export, request.user.id, job_timeout=1200)
        return Response({"status": "Data export job queued."})

    @action(detail=True, methods=["post"])
    def unfollow(self, request, uuid=None):
        try:
            target_profile = Profile.objects.get(uuid=uuid)
        except Profile.DoesNotExist:
            raise PermissionDenied("Profile given does not exist.")
        profile = request.user.profile
        if str(profile.uuid) == uuid:
            raise ValidationError("Cannot unfollow self!")
        profile.following.remove(target_profile)
        return Response({"status": "Unfollowed."})

    @action(detail=True, methods=["get"], permission_classes=(IsAuthenticated,))
    def schedule_update(self, request, uuid):
        try:
            target_profile = Profile.objects.get(uuid=uuid)
        except Profile.DoesNotExist:
            raise PermissionDenied("Profile given does not exist.")
        update_profile(target_profile, force=True)
        return Response({"status": "Scheduled"})

    @action(detail=False, methods=["get"], permission_classes=(IsAuthenticated,))
    def retrieve_export(self, request, pk=None):
        exporter = UserExporter(request.user)
        zipf = exporter.retrieve()
        if not zipf:
            return Response({"status": "No export available"}, status=status.HTTP_400_BAD_REQUEST)
        response = HttpResponse(zipf, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=%s' % exporter.name
        return response

    def _save_sort_order(self, card_ids):
        """Update Content `order` values according to sort order."""
        qs_ids = self.get_queryset().values_list("id", flat=True)
        for i in range(0, len(card_ids)):
            # Only allow updating cards that are in our qs
            card_id = int(card_ids[i])
            if card_id in qs_ids:
                Content.objects.filter(id=card_id).update(order=i)

    @action(detail=False, methods=["post"], permission_classes=(IsAuthenticated,))
    def organize(self, request, uuid=None):
        self._save_sort_order(request.data.get("sort_order").split(","))
        return Response({"status": "Organized."})


class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS and request.version == '2.0'

class UserViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    queryset = User.objects.none()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated|ReadOnly,)

    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=["get"], permission_classes=(IsAdminUser,))
    def recently_active(self, request):
        user_ids = get_recently_active_user_ids()
        users = User.objects.filter(id__in=user_ids)
        users = [UserSerializer(instance=user).data for user in users]
        return JsonResponse(users, safe=False)

    def retrieve(self, request, *args, **kwargs):
        # hack enabling  /u/<username> routes for the SPA UI
        if request.version == '2.0':
            profile = get_object_or_404(Profile, user__username=kwargs.get("pk"))
            serializer = ProfileSerializer(profile, context={'request': request})
            return Response(serializer.data)
        else:
            return super().retrieve(request, *args, **kwargs)
