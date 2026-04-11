import logging

from django.utils.decorators import method_decorator
from django.views.generic.base import View
from federation.entities.activitypub.django.views import activitypub_object_view

logger = logging.getLogger("socialhome")


@method_decorator(activitypub_object_view, name="dispatch")
class ContentView(View):
    pass
