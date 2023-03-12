from django.utils.translation import gettext_lazy as _
from enumfields import Enum


class ContentTarget(Enum):
    # TODO WARNING ContentTarget has been removed. Don't use.
    # Remove code once migrations have been squashed.
    PROFILE = 0


class ContentType(Enum):
    CONTENT = 0
    REPLY = 1
    SHARE = 2

    class Labels:
        CONTENT = _("Content")
        REPLY = _("Reply")
        SHARE = _("Share")

    @property
    def string_value(self):
        return {0: "content", 1: "reply", 2: "share"}.get(self.value)
