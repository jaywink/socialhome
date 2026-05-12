import json

from django.contrib import admin
from django.utils.html import format_html

from django_dramatiq.admin import TaskAdmin
from django_dramatiq.apps import DjangoDramatiqConfig
from django_dramatiq.models import Task
from dramatiq.encoder import JSONEncoder

admin.site.unregister(Task)


@admin.register(Task)
class SafeTaskAdmin(TaskAdmin):
    def message_details(self, instance):
        message_dict = instance.message._asdict()

        dramatiq_encoder = DjangoDramatiqConfig.select_encoder()
        if not isinstance(dramatiq_encoder, JSONEncoder):
            for k, v in message_dict["args"].items():
                message_dict["args"][k] = f"<{v}>"
            for k, v in message_dict["kwargs"].items():
                message_dict["kwargs"][k] = f"<{v}>"

        message_details = json.dumps(message_dict, indent=4)
        return format_html("<pre>{}</pre>", message_details)

    def traceback(self, instance):
        traceback = instance.message.options.get("traceback", None)
        if traceback:
            return format_html("<pre>{}</pre>", traceback)
        return None
