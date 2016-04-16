# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from federation.hostmeta.generators import NODEINFO_DOCUMENT_PATH

from socialhome.federate.views import (
    host_meta_view, webfinger_view, hcard_view, nodeinfo_well_known_view, nodeinfo_view, social_relay_view,
    ReceivePublicView)


urlpatterns = [
    # Discovery
    url(r'^.well-known/host-meta$', host_meta_view, name="host-meta"),
    url(r'^webfinger$', webfinger_view, name="webfinger"),
    url(r"^hcard/users/(?P<guid>[^/]+)$", hcard_view, name="hcard"),
    url(r"^.well-known/nodeinfo$", nodeinfo_well_known_view, name="nodeinfo-wellknown"),
    url(NODEINFO_DOCUMENT_PATH.lstrip("/"), nodeinfo_view, name="nodeinfo"),
    url(r"^.well-known/x-social-relay$", social_relay_view, name="social-relay"),

    # Payloads
    url(r"^receive/public/$", csrf_exempt(ReceivePublicView.as_view()), name="receive-public"),
    # Ensure post without trailing slash works, some Diaspora speaking servers do this
    # Django would redirect to a slashflul url anyway but the docs warn of potential POST data loss
    url(r"^receive/public$", csrf_exempt(ReceivePublicView.as_view())),
]
