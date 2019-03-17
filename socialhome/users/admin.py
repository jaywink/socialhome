from django.contrib import admin
from django.contrib.admin import ModelAdmin

from socialhome.users.models import User, Profile


@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    list_display = ('id', 'uuid', 'name', 'handle', 'fid', 'visibility', 'user', 'protocol')
    list_filter = ('visibility', 'protocol')
    raw_id_fields = ('user', 'following', 'followed_tags')
    readonly_fields = ('uuid', 'fid', 'guid', 'handle', 'rsa_public_key')
    search_fields = ('id', 'uuid', 'name', 'handle', 'email', 'fid')
    list_select_related = ('user',)


@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('id', 'username', 'name', 'trusted_editor')
    list_filter = ('trusted_editor',)
    search_fields = ('id', 'name', 'username')
