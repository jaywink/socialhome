from django.views.generic import ListView

from socialhome.content.models import Content
from socialhome.enums import Visibility


class BaseStreamView(ListView):
    model = Content
    ordering = "-created"
    paginate_by = 30


class PublicStreamView(BaseStreamView):
    template_name = "streams/public.html"
    queryset = Content.objects.filter(visibility=Visibility.PUBLIC)
