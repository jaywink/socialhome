from django.db.models import QuerySet, Q

from socialhome.enums import Visibility


class ProfileQuerySet(QuerySet):
    def visible_for_user(self, user):
        if not user.is_authenticated:
            return self.filter(visibility=Visibility.PUBLIC)
        # TODO: handle also LIMITED when contacts implemented
        return self.filter(Q(id=user.profile.id) | Q(visibility__in=[Visibility.SITE, Visibility.PUBLIC]))
