from django.contrib import admin
from django.contrib.admin import ModelAdmin

from socialhome.federate.models import Payload


@admin.register(Payload)
class PayloadAdmin(ModelAdmin):
    list_display = ('id', 'entities_found', 'protocol', 'direction', 'method', 'url', 'created')
    list_filter = ('entities_found', 'direction', 'protocol', 'method', 'created')
    search_fields = ('body', 'sender', 'url')
