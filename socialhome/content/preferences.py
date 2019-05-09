from django.utils.translation import ugettext_lazy as _
from dynamic_preferences.types import Section, BooleanPreference
from dynamic_preferences.users.registries import user_preferences_registry

content = Section("content")


@user_preferences_registry.register
class UseNewPublisher(BooleanPreference):
    section = content
    name = "use_new_publisher"
    default = False
    verbose_name = _("Use new publisher")
    help_text = _("Set this to use the new alpha publisher when possible. "
                  "Warning! Not all functionality is available in the new publisher.")
