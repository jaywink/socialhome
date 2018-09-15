from typing import Dict, Tuple, TYPE_CHECKING, Any

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet, Q

from socialhome.enums import Visibility

if TYPE_CHECKING:
    from socialhome.users.models import Profile


class ProfileQuerySet(QuerySet):
    def fed(self, value: str) -> 'Profile':
        """
        Get Profile by federated ID.
        """
        return self.get(
            Q(fid=value) | Q(guid=value) | Q(handle=value)
        )

    def fed_update_or_create(self, fid: str, values: Dict[str, Any], extra_lookups: Dict=None) -> Tuple['Profile', bool]:
        """
        Update or create by federated ID.
        """
        if extra_lookups:
            qs = self.filter(**extra_lookups)
        else:
            qs = self
        try:
            profile = qs.fed(fid)
        except ObjectDoesNotExist:
            return self.create(**values), True
        else:
            for key, value in values.items():
                if key in ('fid', 'guid', 'handle'):
                    continue
                setattr(profile, key, value)
            profile.save()
            return profile, False

    def followers(self, profile):
        """Return followers of a Profile."""
        return self.filter(following=profile)

    def visible_for_user(self, user):
        if not user.is_authenticated:
            return self.filter(visibility=Visibility.PUBLIC)
        if user.is_staff:
            return self
        return self.filter(Q(id=user.profile.id) | Q(visibility__in=[
            Visibility.LIMITED, Visibility.SITE, Visibility.PUBLIC
        ]))
