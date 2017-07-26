from django.db.models import QuerySet, Q

from socialhome.enums import Visibility


class ProfileQuerySet(QuerySet):
    def visible_for_user(self, user):
        if not user.is_authenticated:
            return self.filter(visibility=Visibility.PUBLIC)
        if user.is_staff:
            return self
        return self.filter(Q(id=user.profile.id) | Q(visibility__in=[
            Visibility.LIMITED, Visibility.SITE, Visibility.PUBLIC
        ]))

    def followers(self, profile):
        """Return followers of a Profile."""
        return self.filter(following=profile)
