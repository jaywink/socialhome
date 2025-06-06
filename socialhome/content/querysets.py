from typing import Dict, Tuple, TYPE_CHECKING, Any

from django.db import models
from django.db.models import Q, F, OuterRef, Subquery, Case, When, ObjectDoesNotExist
from django.db.utils import IntegrityError

from socialhome.content.enums import ContentType
from socialhome.enums import Visibility
from socialhome.users.models import User

if TYPE_CHECKING:
    from socialhome.content.models import Content


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
    def full_conversation(self, parent_id, user):
        """Return replies for a Content visible to user..

        Returns the direct replies and all replies for shares.
        """
        qs = self.filter(content_type=ContentType.REPLY).visible_for_user(user)
        ids = qs.filter(root_parent_id=parent_id).values_list("id", flat=True)
        share_ids = qs.filter(root_parent__share_of_id=parent_id).values_list("id", flat=True)
        all_ids = list(ids) + list(share_ids)
        return qs.filter(id__in=all_ids).order_by("created")

    def children(self, parent_id, user):
        """Return replies for a Content visible to user..

        Returns the direct replies and all replies for shares.
        """
        qs = self.filter(content_type=ContentType.REPLY).visible_for_user(user)
        ids = qs.filter(parent_id=parent_id).values_list("id", flat=True)
        share_ids = qs.filter(parent__share_of_id=parent_id).values_list("id", flat=True)
        all_ids = list(ids) + list(share_ids)
        return qs.filter(id__in=all_ids).order_by("created")

    def fed(self, value: str, **params) -> models.QuerySet:
        """
        Get Content by federated ID.
        """
        return self.filter(
            Q(fid=value) | Q(guid=value)
        ).filter(**params)

    def fed_update_or_create(
        self, fid: str, values: Dict[str, Any], extra_lookups: Dict = None
    ) -> Tuple['Content', bool]:
        """
        Update or create by federated ID.
        """
        if not extra_lookups:
            extra_lookups = {}
        try:
            content = self.fed(fid, **extra_lookups).get()
        except ObjectDoesNotExist:
            if fid.startswith('http'):
                values['fid'] = fid
            values.update(extra_lookups)
            return self.create(**values), True
        else:
            for key, value in values.items():
                if key in ('fid', 'guid'):
                    continue
                setattr(content, key, value)
            content.save()
            return content, False

    def followed(self, user, single_id: int = None):
        """Get content from followed users.

        This includes content shared by the followed users.
        """
        profile = user.profile
        following_ids = profile.following.values_list("id", flat=True)
        qs = self.top_level()
        if single_id:
            qs = qs.filter(id=single_id)
        qs = qs.filter(
            Q(shares__author_id__in=following_ids) | Q(author_id__in=following_ids)
        )
        return qs.visible_for_user(user)

    def limited(self, user, single_id: int = None):
        qs = self.top_level()
        if single_id:
            qs = qs.filter(id=single_id)
        return qs.visible_for_user(user).filter(visibility=Visibility.LIMITED)

    def local(self, user, single_id: int = None):
        qs = self.top_level()
        if single_id:
            qs = qs.filter(id=single_id)
        return qs.visible_for_user(user).filter(local=True)

    def pinned(self):
        return self.filter(pinned=True)

    def profile(self, profile, user, include_shares=True, single_id: int = None):
        """Filter for a user profile.

        Ensures if the profile is not visible to the user, no content will be returned.

        If "single_id" given, check is done against that content only.
        """
        from socialhome.content.models import Content
        if not profile.visible_to_user(user):
            return Content.objects.none()
        qs = self.top_level()
        if single_id:
            qs = qs.filter(id=single_id)
        ids = qs.filter(author=profile).values_list("id", flat=True)
        if include_shares:
            ids = list(ids) + list(Content.objects.filter(shares__author=profile).values_list("id", flat=True))
        qs = qs.filter(
            Q(id__in=ids) | Q(share_of_id__in=ids)
        )
        return qs.visible_for_user(user)

    def profile_by_attr(self, attr, value, user, include_shares=True):
        """Filter for a user profile by attribute.

        Ensures if the profile is not visible to the user, no content will be returned.
        """
        from socialhome.content.models import Content
        from socialhome.users.models import Profile
        get_by = {attr: value}
        try:
            profile = Profile.objects.get(**get_by)
        except Profile.DoesNotExist:
            return Content.objects.none()
        return self.profile(profile, user, include_shares=include_shares)

    def profile_pinned(self, profile, user, single_id: int = None):
        """Get profile content user has chosen to pin on profile."""
        return self.profile(profile, user, include_shares=False, single_id=single_id).pinned()

    def profile_pinned_by_attr(self, attr, value, user):
        """Get profile content user has chosen to pin on profile."""
        return self.profile_by_attr(attr, value, user, include_shares=False).pinned()

    def public(self, single_id: int = None):
        qs = self.top_level()
        if single_id:
            qs = qs.filter(id=single_id)
        return qs.filter(visibility=Visibility.PUBLIC)

    def shares(self, share_of_id, user):
        qs = self.visible_for_user(user).filter(share_of_id=share_of_id)
        return qs.order_by("created")

    def tag(self, tag, user, single_id: int = None):
        qs = self.top_level()
        if single_id:
            qs = qs.filter(id=single_id)
        return qs.visible_for_user(user).filter(tags=tag)

    def tag_by_name(self, tag, user):
        from socialhome.content.models import Tag, Content
        try:
            tag = Tag.objects.get_by_cleaned_name(tag)
        except Tag.DoesNotExist:
            return Content.objects.none()
        return self.tag(tag, user)

    def tags_followed_by_user(self, user, single_id=None):
        # type: (User, int) -> ContentQuerySet
        if not user.is_authenticated:
            return self.none()
        qs = self.top_level().visible_for_user(user)
        if single_id:
            qs = qs.filter(id=single_id)
        return qs.filter(tags__in=user.profile.followed_tags.all())

    def top_level(self):
        # type: () -> ContentQuerySet
        return self.filter(content_type=ContentType.CONTENT)

    def visible_for_user(self, user):
        # type: (User) -> ContentQuerySet
        """Filter by visibility to given user."""
        if not user.is_authenticated:
            return self.filter(visibility=Visibility.PUBLIC)
        return self.filter(
            Q(author=user.profile) |
            Q(visibility__in=[Visibility.SITE, Visibility.PUBLIC]) |
            (
                Q(visibility=Visibility.LIMITED) &
                Q(limited_visibilities=user.profile)
            )
        ).distinct()
