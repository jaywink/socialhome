import warnings

from django.utils.translation import ugettext_lazy as _
from enumfields import Enum


class ContentTarget(Enum):
    PROFILE = 0

    warnings.warn("ContentTarget has been removed. "
                  "Remove code once migrations have been squashed.", UserWarning)


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
