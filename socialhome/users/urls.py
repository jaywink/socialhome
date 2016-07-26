# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        regex=r'^$',
        view=views.UserListView.as_view(),
        name='list'
    ),
    url(
        regex=r'^~redirect/$',
        view=views.UserRedirectView.as_view(),
        name='redirect'
    ),
    url(
        regex=r'^(?P<nickname>[\w.@+-]+)/$',
        view=views.ProfileDetailView.as_view(),
        name='detail'
    ),
    url(
        regex=r'^~organize/$',
        view=views.OrganizeContentProfileDetailView.as_view(),
        name='detail-organize'
    ),
    url(
        regex=r'^~update/$',
        view=views.ProfileUpdateView.as_view(),
        name='update'
    ),
]
