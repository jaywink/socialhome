from typing import Dict, Tuple, TYPE_CHECKING, Any

from django.db.models import QuerySet, Q, ObjectDoesNotExist
from django.db.utils import IntegrityError

from socialhome.enums import Visibility

if TYPE_CHECKING:
    from socialhome.users.models import Profile


class ProfileQuerySet(QuerySet):
    def active_local(self) -> QuerySet:
        """
        Get profiles of active local users.
        """
        return self.filter(
            user__isnull=False,
            user__is_active=True,
        )

    def fed(self, value: str, **params) -> QuerySet:
        """
        Get Profile by federated ID.
        """
        return self.filter(
            Q(fid=value) | Q(guid=value) | Q(handle=value) | Q(finger__iexact=value)
        ).filter(**params)

    def fed_update_or_create(
        self, fid: str, values: Dict[str, Any], extra_lookups: Dict = None, force: bool = False
    ) -> Tuple['Profile', bool]:
        """
        Update or create by federated ID.
        """
        if not extra_lookups:
            extra_lookups = {}

        qs1 = self.fed(fid, **extra_lookups)
        # Some platforms (hello firefish) allow fid updates while keeping
        # the same finger and remote_url properties. Is it ok to assumes
        # finger and remote_url are never updated?
        qs2 = self.filter(finger=values.get('finger', ''), remote_url=values.get('remote_url', ''))
        if qs1.count():
            profile = qs1.get()
        elif qs2.count():
            profile = qs2.get()
        else:
            profile = None

        if fid.startswith('http'):
            values['fid'] = fid
        if not profile:
            values.update(extra_lookups)
            return self.create(**values), True
        else:
            changed = False
            for key, value in values.items():
                if key in ('guid', 'handle'):
                    continue
                if getattr(profile, key, None) != value:
                    changed = True
                    setattr(profile, key, value)
            # Switch profile to ActivityPub if Diaspora and we got an ActivityPub payload,
            # indicating this is a multi-protocol remote
            if profile.protocol == "diaspora" and profile.fid:
                profile.protocol = "activitypub"
                changed = True
            if changed or force:
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
