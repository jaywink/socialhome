from django.contrib import admin
from django.contrib.admin import ModelAdmin

from socialhome.users.models import User, Profile


@admin.register(Profile)
class ProfileAdmin(ModelAdmin):
    list_display = ('id', 'guid', 'name', 'handle', 'fid', 'visibility', 'user')
    list_filter = ('visibility',)
    raw_id_fields = ('user', 'following')
    search_fields = ('id', 'guid', 'name', 'handle', 'email', 'fid')
    list_select_related = ('user',)


@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ('id', 'username', 'name', 'trusted_editor')
    list_filter = ('trusted_editor',)
    raw_id_fields = ('followers', 'following')
    search_fields = ('id', 'name', 'username')
