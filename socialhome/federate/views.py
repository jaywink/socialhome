# -*- coding: utf-8 -*-
from django.conf import settings
from django.http import HttpResponse
from django.http.response import Http404
from django.shortcuts import get_object_or_404

from federation.hostmeta.generators import generate_host_meta, generate_legacy_webfinger
from socialhome.users.models import User


def host_meta_view(request):
    """Generate a `.well-known/host-meta` document"""
    host_meta = generate_host_meta("diaspora", webfinger_host=settings.SOCIALHOME_DOMAIN)
    return HttpResponse(host_meta, content_type="application/xrd+xml")


def webfinger_view(request):
    """Generate a webfinger document."""
    q = request.GET.get("q")
    if not q:
        return Http404
    user = get_object_or_404(User, username=q.split("@")[0])
    # Create webfinger document
    webfinger = generate_legacy_webfinger(
        "diaspora",
        handle="{username}@{domain}".format(username=user.username, domain=settings.SOCIALHOME_DOMAIN),
        host=settings.SOCIALHOME_DOMAIN,
        guid=user.guid,
        public_key=user.rsa_public_key
    )
    return HttpResponse(webfinger, content_type="application/xrd+xml")
