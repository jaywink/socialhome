from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from federation.utils.text import validate_handle
from markdownx.widgets import MarkdownxWidget

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.content.utils import safe_text_for_markdown
from socialhome.enums import Visibility
from socialhome.users.models import Profile


class ContentForm(forms.ModelForm):
    recipients = forms.CharField(required=False, label=_("Recipients"))

    class Meta:
        model = Content
        fields = [
            "text", "visibility", "pinned", "show_preview", "federate", "include_following",
            "recipients",
        ]
        widgets = {
            "text": MarkdownxWidget()
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        is_reply = kwargs.pop("is_reply", False)
        super(ContentForm, self).__init__(*args, **kwargs)
        if is_reply:
            self.fields.pop("visibility")
            self.fields.pop("pinned")
            self.fields.pop("federate")
            self.fields.pop("recipients")
            self.fields.pop("include_following")
        else:
            self.fields["visibility"].widget.attrs = {"class": "form-control"}
            self.fields["pinned"].widget.attrs = {"class": "form-check"}
            self.fields["federate"].widget.attrs = {"class": "form-check"}
            self.fields["recipients"].widget.attrs = {"class": "form-control"}
            self.fields["include_following"].widget.attrs = {"class": "form-check"}
        self.fields["show_preview"].widget.attrs = {"class": "form-check"}
        self.fields["text"].widget.attrs = {"class": "form-control"}

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('visibility') == Visibility.LIMITED:
            if not cleaned_data.get('recipients') and not cleaned_data.get('include_following'):
                self.add_error('recipients', _('Recipients cannot be empty if not including followed users.'))

    def clean_recipients(self):
        """
        Check recipients can be found.
        """
        if self.cleaned_data.get('visibility') != Visibility.LIMITED or not self.cleaned_data.get('recipients'):
            return ""

        recipients = [r.strip() for r in self.cleaned_data.get('recipients', '').split(',')]

        for recipient in recipients:
            if not validate_handle(recipient):
                raise ValidationError(_("Recipient %s is not in the correct format." % recipient))
        recipient_profiles = Profile.objects.filter(
            Q(handle__in=recipients) | Q(fid__in=recipients)
        ).visible_for_user(self.user)
        # TODO we should probably try to lookup missing ones over the network first before failing
        if recipient_profiles.distinct().count() != len(set(recipients)):
            raise ValidationError(_("Not all recipients could be found."))

        return self.cleaned_data.get('recipients')

    def clean_text(self):
        """Sanitize text if user is untrusted."""
        if self.user.trusted_editor:
            return self.cleaned_data["text"]
        return safe_text_for_markdown(self.cleaned_data["text"])

    def get_initial_for_field(self, field, field_name):
        """
        Add the previous values from limited visibilities for existing limited content.
        """
        if field_name != 'recipients' or not self.instance or self.instance.visibility != Visibility.LIMITED:
            return super().get_initial_for_field(field, field_name)

        recipients = self.instance.limited_visibilities.values_list('handle', flat=True)
        return ",".join(recipients)

    def save(self, commit=True, parent=None):
        """
        Set possible recipients after save.
        """
        # Get previous recipients, if old instance
        previous_recipients = []
        if not self.instance._state.adding and self.instance.limited_visibilities.count():
            previous_recipients = self.instance.limited_visibilities.values_list('id', flat=True)

        if not self.instance.author_id:
            self.instance.author = self.user.profile

        if parent:
            self.instance.parent = parent

        # Save the content
        content = super().save(commit=commit)
        if content.visibility != Visibility.LIMITED or content.content_type == ContentType.SHARE:
            return content

        if content.content_type == ContentType.CONTENT:
            # Collect new recipients
            recipients = [r.strip() for r in self.cleaned_data.get('recipients').split(',')]
            recipients = Profile.objects.filter(handle__in=recipients).visible_for_user(self.user)

            # Add following, if included
            if self.cleaned_data.get('include_following'):
                recipients = recipients | self.user.profile.following.all()
                recipients = recipients.distinct()
        elif content.content_type == ContentType.REPLY:
            recipients = content.parent.limited_visibilities.all()
        else:
            return content

        # If old instance, first remove the now not present to trigger federation retraction
        if previous_recipients:
            to_remove = set(previous_recipients).difference(set(recipients.values_list('id', flat=True)))
            for id in to_remove:
                profile = Profile.objects.get(id=id)
                content.limited_visibilities.remove(profile)

        # Clear, then set, since federation will be triggered by m2m changed signal
        content.limited_visibilities.clear()
        content.limited_visibilities.set(recipients)

        return content
