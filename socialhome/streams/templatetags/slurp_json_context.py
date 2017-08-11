from django.utils.safestring import mark_safe
from django.template import Library
import json

register = Library()


@register.simple_tag(takes_context=True)
def slurp_json_context(context):
    """
    Serializes ``context["json_context"]`` into JSON and generates a JS
    script to attach it to ``window.context``
    Args:
        context: Current view context

    Returns: "<script>window.context = {<context["json_context"]>}</script>"

    """
    return _slurp_json_context(context, lambda obj: str(obj))


@register.simple_tag(takes_context=True)
def slurp_json_context_unsafe(context):
    """
    Has the same behaviour than ``slurp_json_context`` at the exception
    of throwing an error when a variable can't be serialized.
    """
    return _slurp_json_context(context, None)


def _slurp_json_context(context, json_default):
    if context.get("json_context", None) is None:
        return ""

    json_dump = json.dumps(context["json_context"], default=json_default)
    return mark_safe("<script>window.context = %s</script>" % json_dump)
