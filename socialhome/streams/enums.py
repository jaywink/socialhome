from django.utils.translation import gettext_lazy as _
from enumfields import Enum


class StreamType(Enum):
    CONTENT = "content"
    CUSTOM = "custom"
    FOLLOWED = "followed"
    LIMITED = "limited"
    LOCAL = "local"
    PROFILE_ALL = "profile_all"
    PROFILE_PINNED = "profile_pinned"
    PUBLIC = "public"
    TAG = "tag"
    TAGS = "tags"

    class Labels:
        CONTENT = _("Content")
        CUSTOM = _("Custom")
        FOLLOWED = _("Followed")
        LIMITED = _("Limited")
        LOCAL = _("Local")
        PROFILE_ALL = _("Profile (all)")
        PROFILE_PINNED = _("Profile (pinned)")
        PUBLIC = _("Public")
        TAG = _("Tag")
        TAGS = _("Tags")

    @classmethod
    def to_dict(cls):
        return {i.name: i.value for i in cls}
