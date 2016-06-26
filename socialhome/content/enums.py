from django.utils.translation import ugettext_lazy as _
from enumfields import Enum


class ContentTarget(Enum):
    PROFILE = 0


class Visibility(Enum):
    PUBLIC = 0

    class Labels:
        PUBLIC = _("Public")
