from django.template import Library

from socialhome.content.models import Content

register = Library()


@register.filter
def has_shared(content, user):
    if not hasattr(user, "profile"):
        return False
    return Content.has_shared(content.id, user.profile.id)
