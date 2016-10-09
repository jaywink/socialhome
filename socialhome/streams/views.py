from django.views.generic import ListView

from socialhome.enums import Visibility
from socialhome.publisher.models import Content


class BaseStreamView(ListView):
    model = Content
    ordering = "-created"
    paginate_by = 30


class PublicStreamView(BaseStreamView):
    template_name = "streams/public.html"
    queryset = Content.objects.filter(visibility=Visibility.PUBLIC)
