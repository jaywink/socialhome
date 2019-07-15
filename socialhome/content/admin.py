from django.contrib import admin
from django.contrib.admin import ModelAdmin

from socialhome.content.models import Content, Tag


@admin.register(Content)
class ContentAdmin(ModelAdmin):
    list_display = ('id', 'uuid', 'author', 'visibility', 'content_type')
    list_filter = ('content_type', 'visibility', 'pinned', 'service_label', 'local')
    raw_id_fields = ('oembed', 'opengraph', 'mentions', 'tags', 'parent', 'root_parent', 'share_of',
                     'limited_visibilities', 'author')
    readonly_fields = ('content_type', 'local', 'rendered', 'reply_count', 'shares_count', 'uuid', 'fid', 'guid')
    search_fields = ('uuid', 'id', 'author__handle', 'author__name', 'author__fid')
    list_select_related = ('author',)


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("id", "uuid", "name", "created")
    list_filter = ("id", "uuid", "name", "created")
    readonly_fields = ("id", "uuid", "created", "name")
    search_fields = ("id", "uuid", "name")
