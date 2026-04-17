import logging

from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from federation.entities.activitypub.django.views import activitypub_object_view

logger = logging.getLogger("socialhome")


@method_decorator(cache_page(900), name='dispatch')
@method_decorator(vary_on_headers('Accept'), name='dispatch')
@method_decorator(activitypub_object_view, name='dispatch')
class UserDetailView(View):
    pass
