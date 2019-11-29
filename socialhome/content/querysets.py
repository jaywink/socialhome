from typing import Dict, Tuple, TYPE_CHECKING, Any

from django.db import models
from django.db.models import Q, F, OuterRef, Subquery, Case, When, ObjectDoesNotExist

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
    def children(self, parent_id, user):
        """Return replies for a Content visible to user..

        Returns the direct replies and all replies for shares.
        """
        qs = self.visible_for_user(user).filter(content_type=ContentType.REPLY).filter(
            Q(root_parent_id=parent_id) | Q(root_parent__share_of_id=parent_id)
        )
        return qs.order_by("created")

    def fed(self, value: str, **params) -> models.QuerySet:
        """
        Get Content by federated ID.
        """
        return self.filter(
            Q(fid=value) | Q(guid=value)
        ).filter(**params)

    def fed_update_or_create(
        self, fid: str, values: Dict[str, Any], extra_lookups: Dict=None
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

    def followed(self, user):
        """Get content from followed users.

        This includes content shared by the followed users.
        """
        from socialhome.content.models import Content
        profile = user.profile
        following_ids = profile.following.values_list("id", flat=True)
        share = Content.objects.filter(share_of=OuterRef("id")).order_by('-id')
        qs = self.top_level().filter(
            Q(shares__author_id__in=following_ids) | Q(author_id__in=following_ids)
        ).annotate(
            through=Subquery(share.values("id")[:1])
        ).annotate(
            through=Case(
                When(author_id__in=following_ids, then="id"),
                When(through__isnull=False, then="through"),
                default="id",
            )
        )
        return qs.visible_for_user(user)

    def limited(self, user):
        return self.top_level().visible_for_user(user).filter(visibility=Visibility.LIMITED)

    def local(self, user):
        return self.top_level().visible_for_user(user).filter(local=True)

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
        ids = qs.filter(author=profile).values_list("id", flat=True)
        if include_shares:
            ids = list(ids) + list(Content.objects.filter(shares__author=profile).values_list("id", flat=True))
        # Get the right through for the content for shares
        share = Content.objects.filter(share_of=OuterRef("id"), author=profile)
        qs = qs.filter(
            Q(id__in=ids) | Q(share_of_id__in=ids)
        ).annotate(
            through=Subquery(share.values("id")[:1])
        ).annotate(
            through=Case(
                When(through__isnull=False, then='through'),
                default='id',
            )
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

    def profile_pinned(self, profile, user):
        """Get profile content user has chosen to pin on profile."""
        return self.profile(profile, user, include_shares=False).pinned()

    def profile_pinned_by_attr(self, attr, value, user):
        """Get profile content user has chosen to pin on profile."""
        return self.profile_by_attr(attr, value, user, include_shares=False).pinned()

    def public(self):
        return self.top_level().filter(visibility=Visibility.PUBLIC)

    def shares(self, share_of_id, user):
        qs = self.visible_for_user(user).filter(share_of_id=share_of_id)
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

    def tags_followed_by_user(self, user):
        # type: (User) -> ContentQuerySet
        if not user.is_authenticated:
            return self.none()
        qs = self.top_level().visible_for_user(user)
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
        )


class ContentManager(models.Manager.from_queryset(ContentQuerySet)):
    def get_queryset(self):
        # Add a default 'through' to every object. QuerySets will override this when needed
        return super().get_queryset().annotate(through=F("id"))
