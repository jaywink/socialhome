from django.utils.translation import ugettext_lazy as _
from dynamic_preferences.types import Section, BooleanPreference
from dynamic_preferences.users.registries import user_preferences_registry

streams = Section("streams")


@user_preferences_registry.register
class UseNewStream(BooleanPreference):
    section = streams
    name = "use_new_stream"
    default = True
    verbose_name = _("Use new stream")
    help_text = _("Set this to use the new alpha stream when possible. Warning! Not all functionality is available "
                  "in the new stream.")
