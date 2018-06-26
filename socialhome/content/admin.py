from django.contrib import admin
from django.contrib.admin import ModelAdmin

from socialhome.content.models import Content


@admin.register(Content)
class ContentAdmin(ModelAdmin):
    list_display = ('guid', 'author', 'visibility', 'content_type')
    list_filter = ('content_type', 'visibility',)
    raw_id_fields = ('oembed', 'opengraph', 'mentions', 'tags', 'parent', 'share_of')
    search_fields = ('guid',)
    list_select_related = ('author',)
