from django.db import models
from django.db.models import Q, Min, F

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
    def children(self, parent_id, user):
        """Return replies for a Content visible to user..

        Returns the direct replies and all replies for shares.
        """
        qs = self.visible_for_user(user).filter(content_type=ContentType.REPLY).filter(
            Q(parent_id=parent_id) | Q(parent__share_of_id=parent_id)
        )
        return qs.order_by("created")

    def followed(self, user):
        """Get content from followed users.

        This includes content shared by the followed users.
        """
        following_ids = user.profile.following.values_list("id", flat=True)
        qs = self.top_level().filter(Q(shares__author_id__in=following_ids) | Q(author_id__in=following_ids))
        return qs.visible_for_user(user)

    def pinned(self):
        return self.filter(pinned=True)

    def profile(self, profile, user, include_shares=True):
        """Filter for a user profile.

        Ensures if the profile is not visible to the user, no content will be returned.
        """
        from socialhome.content.models import Content
        if not profile.visible_to_user(user):
            return Content.objects.none()
        qs = self.top_level()
        if include_shares:
            qs = qs.filter(Q(shares__author=profile) | Q(author=profile))
        else:
            qs = qs.filter(author=profile)
        return qs.visible_for_user(user)

    def profile_by_attr(self, attr, value, user, include_shares=True):
        """Filter for a user profile by GUID.

        Ensures if the profile is not visible to the user, no content will be returned.
        """
        from socialhome.content.models import Content
        get_by = {attr: value}
        try:
            profile = Profile.objects.get(**get_by)
        except Profile.DoesNotExist:
            return Content.objects.none()
        return self.profile(profile, user, include_shares=include_shares)

    def profile_pinned(self, profile, user):
        """Get profile content user has chosen to pin on profile."""
        return self.profile(profile, user, include_shares=False).pinned()

    def profile_pinned_by_attr(self, attr, value, user):
        """Get profile content user has chosen to pin on profile."""
        return self.profile_by_attr(attr, value, user, include_shares=False).pinned()

    def public(self):
        return self.top_level().filter(visibility=Visibility.PUBLIC)

    def shares(self, share_of_id, user):
        qs = self.visible_for_user(user).filter(share_of_id=share_of_id).annotate(through=Min('id'))
        return qs.order_by("created")

    def tag(self, tag, user):
        return self.top_level().visible_for_user(user).filter(tags=tag)

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


class ContentManager(models.Manager.from_queryset(ContentQuerySet)):
    def get_queryset(self):
        # Add a default 'through' to every object. QuerySets will override this when needed
        return super().get_queryset().annotate(through=F("id"))
