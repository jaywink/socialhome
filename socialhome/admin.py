from django.contrib import admin
from django.core.exceptions import ValidationError
from markdownx.admin import MarkdownxModelAdmin

from socialhome.models import PolicyDocument


@admin.register(PolicyDocument)
class PolicyDocumentAdmin(MarkdownxModelAdmin):
    list_display = ('type', 'state', 'version', 'published_version')

    def save_model(self, request, obj, form, change):
        if obj.state == 'draft':
            obj.edit_draft()
        elif obj.state == 'published':
            if obj.content != obj.published_content:
                obj.publish()
        else:
            raise ValidationError("Invalid state")
        super().save_model(request, obj, form, change)
