from django.utils.translation import gettext_lazy as _
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import Section, BooleanPreference

admin = Section("admin")


@global_preferences_registry.register
class LogAllOutboundPayloads(BooleanPreference):
    section = admin
    name = "log_all_outbound_payloads"
    default = False
    verbose_name = _("Log all outbound payloads")
    help_text = _("If set to true, all outbound payloads will be saved as federate.Payload instances "
                  "(available in the admin). This is a performance hit so should only be turned on for "
                  "temporary debugging.")


@global_preferences_registry.register
class LogAllReceivePayloads(BooleanPreference):
    section = admin
    name = "log_all_receive_payloads"
    default = False
    verbose_name = _("Log all receive payloads")
    help_text = _("If set to true, all inbound payloads will be saved as federate.Payload instances "
                  "(available in the admin). This is a performance hit so should only be turned on for "
                  "temporary debugging.")
