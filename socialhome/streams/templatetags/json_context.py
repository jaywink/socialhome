import json

from django.utils.html import escapejs
from django.utils.safestring import mark_safe
from django.template import Library

register = Library()


@register.simple_tag(takes_context=True)
def json_context(context, raise_error=False):
    """Generate a JS <script> tag from context

    Serializes ``context["json_context"]`` into JSON and generates a JS
    script to attach it to ``window.context``

    If ``raise_error`` is False, values in context that are not
    JSON serialisable will be converted to string. Otherwise, it
    raises TypeError

    :param context: Current view context
    :param raise_error: Control whether to raise an error on non-JSON serialisable values
    :return: ``<script>window.context = JSON.parse('{<context["json_context"]>}');</script>``
    """
    if not context.get("json_context"):
        return ""

    json_default = None if raise_error else lambda obj: str(obj)

    json_dump = json.dumps(context["json_context"], default=json_default)
    return mark_safe("<script>window.context = JSON.parse('%s');</script>" % escapejs(json_dump))
