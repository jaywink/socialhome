# -*- coding: utf-8 -*-
from django.conf.urls import url

from federation.hostmeta.generators import NODEINFO_DOCUMENT_PATH

from socialhome.federate.views import (
    host_meta_view, webfinger_view, hcard_view, nodeinfo_well_known_view, nodeinfo_view)

urlpatterns = [
    url(r'^.well-known/host-meta$', host_meta_view, name="host-meta"),
    url(r'^webfinger$', webfinger_view, name="webfinger"),
    url(r"^hcard/users/(?P<guid>[^/]+)$", hcard_view, name="hcard"),
    url(r"^.well-known/nodeinfo$", nodeinfo_well_known_view, name="nodeinfo-wellknown"),
    url(NODEINFO_DOCUMENT_PATH.lstrip("/"), nodeinfo_view, name="nodeinfo"),
]
