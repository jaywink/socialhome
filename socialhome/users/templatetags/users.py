from django import template

from socialhome.users.tasks.exports import UserExporter

register = template.Library()


@register.simple_tag(takes_context=True)
def get_user_export_date(context):
    exporter = UserExporter(context.get('request').user, context.get('request'))
    try:
        return exporter.file_date
    except Exception:
        pass
