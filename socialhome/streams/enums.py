from django.utils.translation import gettext_lazy as _
from enum_properties import StrEnumProperties


class StreamType(StrEnumProperties):
    label: str

    CONTENT = "content", _("Content")
    CUSTOM = "custom", _("Custom")
    FOLLOWED = "followed", _("Followed")
    LIMITED = "limited", _("Limited")
    LOCAL = "local", _("Local")
    PROFILE_ALL = "profile_all", _("Profile (all)")
    PROFILE_PINNED = "profile_pinned", _("Profile (pinned)")
    PUBLIC = "public", _("Public")
    TAG = "tag", _("Tag")
    TAGS = "tags", _("Tags")

    @classmethod
    def to_dict(cls):
        return {i.name: i.value for i in cls}
