import warnings

from enumfields import Enum


class ContentTarget(Enum):
    PROFILE = 0

    warnings.warn("ContentTarget has been removed. "
                  "Remove code once migrations have been squashed.", UserWarning)
