from django.utils.translation import gettext_lazy as _
from dynamic_preferences.types import Section, ChoicePreference, BooleanPreference
from dynamic_preferences.users.registries import user_preferences_registry

generic = Section("generic")
content = Section("content")


@user_preferences_registry.register
class LandingPage(ChoicePreference):
    """Which page should be shown as landing page?"""
    section = generic
    name = "landing_page"
    choices = [
        ("profile", _("Profile")),
        ("profile_all", _("Profile - all content")),
        ("followed", _("Followed stream")),
        ("local", _("Local stream")),
        ("public", _("Public stream")),
        ("tags", _("Tags stream")),
    ]
    default = "followed"
    verbose_name = _("Landing page")
    help_text = _("Choose which page you want to see as the landing page.")
