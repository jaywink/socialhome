from django.db import models
from django.db.models import Q

from socialhome.enums import Visibility
from socialhome.users.models import Profile


class TagQuerySet(models.QuerySet):
    def get_by_cleaned_name(self, name):
        """Get by name after making sure it's lower case and trimmed."""
        cleaned = name.strip().lower()
        return self.get(name=cleaned)

    def exists_by_cleaned_name(self, name):
        """Exists filter by name after making sure it's lower case and trimmed."""
        cleaned = name.strip().lower()
        return self.filter(name=cleaned).exists()


class ContentQuerySet(models.QuerySet):
    def _select_related(self):
        return self.select_related("oembed", "opengraph")

    def top_level(self):
        return self.filter(parent=None)

    def visible_for_user(self, user):
        """Filter by visibility to given user."""
        if not user.is_authenticated:
            return self.filter(visibility=Visibility.PUBLIC)
        # TODO: handle also LIMITED when contacts implemented
        return self.filter(Q(author=user.profile) | Q(visibility__in=[Visibility.SITE, Visibility.PUBLIC]))

    def public(self):
        return self.top_level()._select_related().filter(visibility=Visibility.PUBLIC).order_by("-created")

    def tags(self, tag, user):
        from socialhome.content.models import Tag, Content
        try:
            tag = Tag.objects.get_by_cleaned_name(tag)
        except Tag.DoesNotExist:
            return Content.objects.none()
        return self.top_level()._select_related().visible_for_user(user).filter(tags=tag).order_by("-created")

    def profile(self, guid, user):
        """Filter for a user profile.

        Ensures if the profile is not visible to the user, no content will be returned.
        """
        from socialhome.content.models import Content
        try:
            profile = Profile.objects.get(guid=guid)
        except Profile.DoesNotExist:
            return Content.objects.none()
        if not profile.visible_to_user(user):
            return Content.objects.none()
        qs = self.top_level()._select_related().visible_for_user(user).filter(pinned=True, author=profile)
        return qs.order_by("order")
