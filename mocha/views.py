from django.conf import settings
from django.views.generic.base import TemplateView


class MochaView(TemplateView):
    template_name = 'mocha/base.html'
    urlname = 'mocha_view'

    def dispatch(self, request, *args, **kwargs):
        config = kwargs.get('config', None)
        if config:
            self.template_name = '{}/tests/{}/mocha.html'.format(kwargs['app'], config)
        else:
            self.template_name = '{}/tests/mocha.html'.format(kwargs['app'])
        return super(MochaView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MochaView, self).get_context_data(**kwargs)
        context["settings"] = settings
        return context
