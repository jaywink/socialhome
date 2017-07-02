from django import template

register = template.Library()


@register.filter
def startswith(value, sub):
    return value.startswith(sub)
