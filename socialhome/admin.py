import django_rq
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from markdownx.admin import MarkdownxModelAdmin

from socialhome.models import PolicyDocument
from socialhome.notifications.tasks import send_policy_document_update_notifications


@admin.register(PolicyDocument)
class PolicyDocumentAdmin(MarkdownxModelAdmin):
    actions = ('send_email',)
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

    def send_email(self, request, queryset):
        types = queryset.values_list('type', flat=True)
        if not types:
            messages.error(request, _("Choose policy document types to send emails about first!"))
            return

        if len(types) == 2:
            docs = 'both'
        else:
            docs = types[0].value

        django_rq.enqueue(send_policy_document_update_notifications, docs)
        messages.info(request, _("Policy document update emails queued for sending."))

    send_email.short_description = _("Send email update to all users")
