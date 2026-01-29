from django.conf.urls import include
from django.urls import re_path
from django.views.decorators.csrf import csrf_exempt

from federation.hostmeta.generators import NODEINFO_DOCUMENT_PATH

from socialhome.federate.views import (
    host_meta_view, webfinger_view, hcard_view, nodeinfo_well_known_view, nodeinfo_view,
    ReceivePublicView, ReceiveUserView, content_xml_view, content_fetch_view)

app_name = 'federate'

urlpatterns = [
    # Federation provided urls
    re_path(r"", include("federation.django.urls")),

    # Discovery
    re_path(r'^.well-known/host-meta$', host_meta_view, name="host-meta"),
    re_path(r'^webfinger$', webfinger_view, name="webfinger"),
    re_path(r"^hcard/users/(?P<uuid>[^/]+)$", hcard_view, name="hcard"),
    re_path(r"^.well-known/nodeinfo$", nodeinfo_well_known_view, name="nodeinfo-wellknown"),
    re_path(NODEINFO_DOCUMENT_PATH.lstrip("/"), nodeinfo_view, name="nodeinfo"),

    # Payloads
    # Ensure post without trailing slash works, some Diaspora speaking servers do this
    # Django would redirect to a slashflul url anyway but the docs warn of potential POST data loss
    re_path(r"^receive/public/$", csrf_exempt(ReceivePublicView.as_view()), name="receive-public"),
    re_path(r"^receive/public$", csrf_exempt(ReceivePublicView.as_view())),
    re_path(r"^receive/users/(?P<uuid>[^/]+)/$", csrf_exempt(ReceiveUserView.as_view()), name="receive-user"),
    re_path(r"^receive/users/(?P<uuid>[^/]+)$", csrf_exempt(ReceiveUserView.as_view())),

    # Content
    re_path(r"^p/(?P<uuid>[^/]+).xml$", content_xml_view, name="content-xml"),
    re_path(r"^fetch/(?P<objtype>[a-z_]+)/(?P<guid>[^/]+)$", content_fetch_view, name="content-fetch"),
]
