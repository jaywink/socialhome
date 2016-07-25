# -*- coding: utf-8 -*-
import logging

from django.conf import settings
from django.http import HttpResponse
from django.http.response import Http404, JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.views.generic import View

from federation.hostmeta.generators import (
    generate_host_meta, generate_legacy_webfinger, generate_hcard, get_nodeinfo_well_known_document, NodeInfo,
    SocialRelayWellKnown)
from federation.protocols.diaspora.protocol import Protocol

from socialhome import __version__ as version
from socialhome.federate.tasks import receive_task
from socialhome.users.models import User

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
        guid=str(user.guid),
        public_key=user.rsa_public_key
    )
    return HttpResponse(webfinger, content_type="application/xrd+xml")


def get_photo_urls():
    """Temporary function to return some pony urls which will not change.

    Once User can have a profile photo and profile updates are sent out, use proper static images urls instead.
    """
    base_url = "{url}{staticpath}images/pony[size].png".format(
        url=settings.SOCIALHOME_URL, staticpath=settings.STATIC_URL
    )
    return base_url.replace("[size]", "300"), base_url.replace("[size]", "100"), base_url.replace("[size]", "50")


def hcard_view(request, guid):
    """Generate a hcard document."""
    try:
        user = get_object_or_404(User, guid=guid)
    except ValueError:
        raise Http404()
    photo300, photo100, photo50 = get_photo_urls()
    hcard = generate_hcard(
        "diaspora",
        hostname=settings.SOCIALHOME_URL,
        fullname=user.name,
        firstname=user.get_first_name(),
        lastname=user.get_last_name(),
        photo300=photo300,
        photo100=photo100,
        photo50=photo50,
        searchable="true" if user.public else "false",
        guid=str(user.guid),
        username=user.username,
        public_key=user.rsa_public_key,
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
