# -*- coding: utf-8 -*-
from django.conf import settings
from django.http import HttpResponse

from federation.hostmeta.generators import generate_host_meta


def host_meta_view(request):
    """Generate a `.well-known/host-meta` document"""
    host_meta = generate_host_meta("diaspora", webfinger_host=settings.SOCIALHOME_DOMAIN)
    return HttpResponse(host_meta, content_type="application/xrd+xml")
