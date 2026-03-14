import typing

from django_enum.drf import EnumField as BaseEnumField
from django.utils.translation import gettext_lazy as _
from enum_properties import Symmetric, IntEnumProperties, StrEnumProperties


class PolicyDocumentType(StrEnumProperties):
    label: str

    TERMS_OF_SERVICE = 'tos', _("Terms of service")
    PRIVACY_POLICY = 'privacypolicy', _("Privacy policy")


class Visibility(IntEnumProperties):
    label: str
    string: typing.Annotated[str, Symmetric(case_fold=True)]

    PUBLIC = 0, _("Public"), "public"
    LIMITED = 1, _("Limited"), "limited"
    SITE = 2, _("Site"), "site"
    SELF = 3, _("Self"), "self"


class EnumField(BaseEnumField):
    """
    There may be a better way to do this, but I haven't found it.
    Allows the selection of an arbitrary property for outgoing serialization.
    """
    representaton = "value"

    def __init__(self, enum, **kwargs):
        self.representation = kwargs.pop("representation", "value")
        super().__init__(enum, **kwargs)

    def to_representation(self, value):
        return getattr(value, self.representation, value)
