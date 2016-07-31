# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.http import HttpResponse
from django.http.response import Http404, JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.generic import View

from federation.hostmeta.generators import (
    generate_host_meta, generate_legacy_webfinger, generate_hcard, get_nodeinfo_well_known_document, NodeInfo,
    SocialRelayWellKnown)
from socialhome import __version__ as version
from socialhome.federate.tasks import receive_task
from socialhome.users.models import User, Profile

logger = logging.getLogger("socialhome")


def host_meta_view(request):
    """Generate a `.well-known/host-meta` document"""
    host_meta = generate_host_meta("diaspora", webfinger_host=settings.SOCIALHOME_URL)
    return HttpResponse(host_meta, content_type="application/xrd+xml")


def webfinger_view(request):
    """Generate a webfinger document."""
    q = request.GET.get("q")
    if not q:
        raise Http404()
    username = q.split("@")[0]
    if username.startswith("acct:"):
        username = username.replace("acct:", "", 1)
    user = get_object_or_404(User, username=username)
    # Create webfinger document
    webfinger = generate_legacy_webfinger(
        "diaspora",
        handle="{username}@{domain}".format(username=user.username, domain=settings.SOCIALHOME_DOMAIN),
        host=settings.SOCIALHOME_URL,
        guid=str(user.profile.guid),
        public_key=user.profile.rsa_public_key
    )
    return HttpResponse(webfinger, content_type="application/xrd+xml")


def hcard_view(request, guid):
    """Generate a hcard document.

    For local users only.
    """
    try:
        profile = get_object_or_404(Profile, guid=guid, user__isnull=False)
    except ValueError:
        raise Http404()
    photo300, photo100, photo50 = profile.get_image_urls()
    hcard = generate_hcard(
        "diaspora",
        hostname=settings.SOCIALHOME_URL,
        fullname=profile.name,
        firstname=profile.get_first_name(),
        lastname=profile.get_last_name(),
        photo300=photo300,
        photo100=photo100,
        photo50=photo50,
        searchable="true" if profile.public else "false",
        guid=profile.guid,
        username=profile.user.username,
        public_key=profile.rsa_public_key,
    )
    return HttpResponse(hcard)


def nodeinfo_well_known_view(request):
    """Generate .well-known/nodeinfo."""
    wellknown = get_nodeinfo_well_known_document(settings.SOCIALHOME_URL)
    return JsonResponse(wellknown)


def nodeinfo_view(request):
    """Generate a NodeInfo document."""
    nodeinfo = NodeInfo(
        software={"name": "socialhome", "version": version},
        protocols={"inbound": ["diaspora"], "outbound": ["diaspora"]},
        services={"inbound": [], "outbound": []},
        open_registrations=settings.ACCOUNT_ALLOW_REGISTRATION,
        usage={"users": {}},
        metadata={"nodeName": "Socialhome"}
    )
    return JsonResponse(nodeinfo.doc)


def social_relay_view(request):
    """Generate a .well-known/x-social-relay document."""
    relay = SocialRelayWellKnown(subscribe=True)
    return JsonResponse(relay.doc)


class ReceivePublicView(View):
    """Diaspora /receive/public view."""
    def post(self, request, *args, **kwargs):
        payload = request.POST.get("xml")
        if not payload:
            return HttpResponseBadRequest()
        receive_task.delay(payload)
        return HttpResponse(status=202)


class ReceiveUserView(View):
    """Diaspora /receive/users view."""
    def post(self, request, *args, **kwargs):
        payload = request.POST.get("xml")
        if not payload:
            return HttpResponseBadRequest()
        guid = kwargs.get("guid")
        receive_task.delay(payload, guid=guid)
        return HttpResponse(status=202)
