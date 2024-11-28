import xml

from django.db.models import Count
from django.shortcuts import redirect
from django.urls import reverse
from rest_framework.response import Response

from federation.entities import base
from federation.fetchers import retrieve_remote_profile, retrieve_remote_content
from federation.utils.text import validate_handle
from socialhome.content.models import Tag, Content
from socialhome.federate.utils import process_entities
from socialhome.users.models import Profile
from socialhome.users.utils import update_profile
from socialhome.utils import is_url


def get_single_object(q, request, api=False, *args, **kwargs):
    if q.startswith('#'):
        q = q.lower()
        try:
            tag = Tag.objects.filter(
                name=q[1:]
            ).annotate(
                content_count=Count('contents')
            ).filter(
                content_count__gt=0
            ).get()
        except Tag.DoesNotExist:
            pass
        else:
            return Response({'count':1, 'next':None, 'results':[{'name': tag.name}]}) \
                if api else redirect(tag.get_absolute_url())
    # Check if profile matches
    profile = None
    try:
        profile = Profile.objects.visible_for_user(request.user).fed(q).get()
        update_profile(profile)
    except Profile.DoesNotExist:
        # Try a remote search
        if is_url(q) or validate_handle(q):
            try:
                remote_profile = retrieve_remote_profile(q)
            except (AttributeError, ValueError, xml.parsers.expat.ExpatError):
                # Catch various errors parsing the remote profile
                return None
            if remote_profile and isinstance(remote_profile, base.Profile):
                profile = Profile.from_remote_profile(remote_profile)
    if profile:
        return Response({'count':1, 'next':None, 'results':[{'finger': profile.finger, 'uuid': profile.uuid}]}) \
            if api else redirect(reverse("users:profile-detail", kwargs={"uuid": profile.uuid}))
    # Check if content matches
    content = None
    try:
        content = Content.objects.visible_for_user(request.user).fed(q).get()
    except Content.DoesNotExist:
        # Try a remote search
        if is_url(q):
            try:
                remote_content = retrieve_remote_content(q)
            except (AttributeError, ValueError):
                # Catch various errors parsing the remote content
                return None
            if remote_content:
                process_entities([remote_content])
                # Try again
                try:
                    content = Content.objects.visible_for_user(request.user).fed(remote_content.id).get()
                except Content.DoesNotExist:
                    return None
    if content:
        return Response({'count':1, 'next':None, 'results': [{'id': content.id}]}) \
            if api else redirect(reverse("content:view", kwargs={"pk": content.id}))

