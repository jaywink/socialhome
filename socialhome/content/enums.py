import typing

from django.utils.translation import gettext_lazy as _
from enum_properties import Symmetric, IntEnumProperties


class ContentTarget(IntEnumProperties):
    # TODO WARNING ContentTarget has been removed. Don't use.
    # Remove code once migrations have been squashed.
    PROFILE = 0


class ContentType(IntEnumProperties):
    label: str
    string: typing.Annotated[str, Symmetric(case_fold=True)]

    CONTENT = 0, _("Content"), "content"
    REPLY = 1, _("Reply"), "reply"
    SHARE = 2, _("Share"), "share"
