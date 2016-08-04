from django.views.generic import ListView

from socialhome.content.models import Content
from socialhome.enums import Visibility


class BaseStreamView(ListView):
    model = Content
    ordering = "-created"
    paginate_by = 20


class PublicStreamView(BaseStreamView):
    template_name = "streams/public.html"

    def get_queryset(self):
        return Content.objects.filter(visibility=Visibility.PUBLIC)
