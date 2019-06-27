from django.contrib import admin
from django.contrib.admin import ModelAdmin

from socialhome.activities.models import Activity


@admin.register(Activity)
class ActivityAdmin(ModelAdmin):
    list_display = ('id', 'type', 'content_type', 'fid', 'profile', 'created')
    list_filter = ('type', 'content_type', 'created')
    search_fields = ('profile', 'fid')
