# -*- coding: utf-8 -*-
from django.conf.urls import url

from socialhome.federate.views import host_meta_view, webfinger_view


urlpatterns = [
    url(r'^.well-known/host-meta$', host_meta_view, name="host-meta"),
    url(r'^webfinger$', webfinger_view, name="webfinger"),
]
