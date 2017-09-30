from django import template

register = template.Library()


@register.filter
def dict_value(dictionary, key):
    # TODO remove safety once profile streams have throughs too
    if not dictionary:
        return
    return dictionary.get(key)
