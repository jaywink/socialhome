# -*- coding: utf-8 -*-
import logging

import django_rq
from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpResponse
from django.http.response import Http404, JsonResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import View

from federation.entities.diaspora.utils import get_full_xml_representation
from federation.hostmeta.generators import (
    generate_host_meta, generate_legacy_webfinger, generate_hcard, get_nodeinfo_well_known_document, NodeInfo,
    SocialRelayWellKnown)
from federation.protocols.diaspora.magic_envelope import MagicEnvelope

from socialhome import __version__ as version
from socialhome.content.models import Content
from socialhome.enums import Visibility
from socialhome.federate.tasks import receive_task
from socialhome.federate.utils.tasks import make_federable_entity
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
    site = Site.objects.get_current()
    nodeinfo = NodeInfo(
        software={"name": "socialhome", "version": version},
        protocols={"inbound": ["diaspora"], "outbound": ["diaspora"]},
        services={"inbound": [], "outbound": []},
        open_registrations=settings.ACCOUNT_ALLOW_REGISTRATION,
        usage={"users": {}},
        metadata={"nodeName": site.name}
    )
    return JsonResponse(nodeinfo.doc)


def social_relay_view(request):
    """Generate a .well-known/x-social-relay document."""
    relay = SocialRelayWellKnown(subscribe=True)
    return JsonResponse(relay.doc)


def content_xml_view(request, guid):
    """Diaspora single post view XML representation.

    Fetched by remote servers in certain situations.
    """
    content = get_object_or_404(Content, guid=guid, visibility=Visibility.PUBLIC)
    entity = make_federable_entity(content)
    return HttpResponse(get_full_xml_representation(entity), content_type="application/xml")


def content_fetch_view(request, objtype, guid):
    """Diaspora content fetch view.

    Returns the signed payload for the public content. Non-public content will return 404.

    If the content is not local, redirect to content author server.

    Args:
        objtype (str) - Diaspora content type. Currently if it is `status_message`, `post` or `reshare`,
            we try to find `Content`.
        guid (str) - The object guid to look for.
    """
    if objtype not in ["status_message", "post", "reshare"]:
        raise Http404()
    content = get_object_or_404(Content, guid=guid, visibility=Visibility.PUBLIC)
    if not content.is_local:
        url = "https://%s/fetch/%s/%s" % (
            content.author.handle.split("@")[1], objtype, guid
        )
        return HttpResponseRedirect(url)
    entity = make_federable_entity(content)
    message = get_full_xml_representation(entity)
    document = MagicEnvelope(
        message=message, private_key=content.author.private_key, author_handle=content.author.handle
    )
    return HttpResponse(document.render(), content_type="application/magic-envelope+xml")


class ReceivePublicView(View):
    """Diaspora /receive/public view."""
    def post(self, request, *args, **kwargs):
        payload = request.POST.get("xml")
        if not payload:
            return HttpResponseBadRequest()
        django_rq.enqueue(receive_task, payload)
        return HttpResponse(status=202)


class ReceiveUserView(View):
    """Diaspora /receive/users view."""
    def post(self, request, *args, **kwargs):
        payload = request.POST.get("xml")
        if not payload:
            return HttpResponseBadRequest()
        guid = kwargs.get("guid")
        django_rq.enqueue(receive_task, payload, guid=guid)
        return HttpResponse(status=202)
