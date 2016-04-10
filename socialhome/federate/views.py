# -*- coding: utf-8 -*-
from django.conf import settings
from django.http import HttpResponse
from django.http.response import Http404
from django.shortcuts import get_object_or_404

from federation.hostmeta.generators import generate_host_meta, generate_legacy_webfinger, generate_hcard
from socialhome.users.models import User


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


def hcard_view(request, guid):
    """Generate a hcard document."""
    try:
        user = get_object_or_404(User, guid=guid)
    except ValueError:
        raise Http404()
    hcard = generate_hcard(
        "diaspora",
        hostname=settings.SOCIALHOME_URL,
        fullname=user.name,
        firstname=user.get_first_name(),
        lastname=user.get_last_name(),
        photo300="",
        photo100="",
        photo50="",
        searchable="true"  # TODO: allow user to set this
    )
    return HttpResponse(hcard)
