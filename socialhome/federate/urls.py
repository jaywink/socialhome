# -*- coding: utf-8 -*-
from django.conf.urls import url

from .views import host_meta_view

urlpatterns = [
    url(r'^.well-known/host-meta$', host_meta_view),
]
