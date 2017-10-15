from django.db import models
from django.db.models import Q

from socialhome.content.enums import ContentType
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

    def children(self, parent_id, user):
        from socialhome.content.models import Content
        base_qs = self._select_related().visible_for_user(user)
        share_ids = Content.objects.filter(share_of_id=parent_id).values_list("id", flat=True)
        # Immediate replies to parent and replies to shares
        qs = base_qs.filter(parent_id=parent_id) | base_qs.filter(parent_id__in=share_ids)
        return qs.order_by("created")

    def followed(self, user):
        """Get content from followed users.

        This includes content shared by the followed users.
        """
        following_ids = user.profile.following.values_list("id", flat=True)
        qs = self.top_level().filter(Q(shares__author_id__in=following_ids) | Q(author_id__in=following_ids))
        return qs._select_related().visible_for_user(user)

    def pinned(self):
        return self.filter(pinned=True)

    def profile(self, profile, user):
        """Filter for a user profile.

        Ensures if the profile is not visible to the user, no content will be returned.
        """
        from socialhome.content.models import Content
        if not profile.visible_to_user(user):
            return Content.objects.none()
        qs = self.top_level().filter(Q(shares__author=profile) | Q(author=profile))
        return qs._select_related().visible_for_user(user)

    def profile_by_attr(self, attr, value, user):
        """Filter for a user profile by GUID.

        Ensures if the profile is not visible to the user, no content will be returned.
        """
        from socialhome.content.models import Content
        get_by = {attr: value}
        try:
            profile = Profile.objects.get(**get_by)
        except Profile.DoesNotExist:
            return Content.objects.none()
        return self.profile(profile, user)

    def profile_pinned(self, profile, user):
        """Get profile content user has chosen to pin on profile."""
        return self.profile(profile, user).pinned()

    def profile_pinned_by_attr(self, attr, value, user):
        """Get profile content user has chosen to pin on profile."""
        return self.profile_by_attr(attr, value, user).pinned()

    def public(self):
        return self.top_level()._select_related().filter(visibility=Visibility.PUBLIC)

    def tag(self, tag, user):
        return self.top_level()._select_related().visible_for_user(user).filter(tags=tag)

    def tag_by_name(self, tag, user):
        from socialhome.content.models import Tag, Content
        try:
            tag = Tag.objects.get_by_cleaned_name(tag)
        except Tag.DoesNotExist:
            return Content.objects.none()
        return self.tag(tag, user)

    def top_level(self):
        return self.filter(content_type=ContentType.CONTENT)

    def visible_for_user(self, user):
        """Filter by visibility to given user."""
        if not user.is_authenticated:
            return self.filter(visibility=Visibility.PUBLIC)
        # TODO: handle also LIMITED when contacts implemented
        return self.filter(Q(author=user.profile) | Q(visibility__in=[Visibility.SITE, Visibility.PUBLIC]))
