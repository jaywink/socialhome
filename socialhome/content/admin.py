from django.contrib import admin
from django.contrib.admin import ModelAdmin

from socialhome.content.models import Content


@admin.register(Content)
class ContentAdmin(ModelAdmin):
    list_display = ('id', 'uuid', 'author', 'visibility', 'content_type')
    list_filter = ('content_type', 'visibility', 'pinned', 'service_label', 'local')
    raw_id_fields = ('oembed', 'opengraph', 'mentions', 'tags', 'parent', 'share_of', 'limited_visibilities', 'author')
    search_fields = ('uuid', 'id', 'author__handle', 'author__name')
    list_select_related = ('author',)
