import logging

from django.conf import settings
from federation.entities import base

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.enums import Visibility
from socialhome.users.models import Profile

logger = logging.getLogger("socialhome")


def _make_post(content):
    try:
        return base.Post(
            raw_content=content.text,
            guid=str(content.guid),
            handle=content.author.handle,
            public=True if content.visibility == Visibility.PUBLIC else False,
            provider_display_name="Socialhome",
            created_at=content.effective_modified,
        )
    except Exception as ex:
        logger.exception("_make_post - Failed to convert %s: %s", content.guid, ex)
        return None


def _make_comment(content):
    try:
        return base.Comment(
            raw_content=content.text,
            guid=str(content.guid),
            target_guid=str(content.parent.guid),
            handle=content.author.handle,
            created_at=content.effective_modified,
        )
    except Exception as ex:
        logger.exception("_make_comment - Failed to convert %s: %s", content.guid, ex)
        return None


def _make_share(content):
    try:
        return base.Share(
            raw_content=content.text,
            guid=str(content.guid),
            target_guid=str(content.share_of.guid),
            handle=content.author.handle,
            target_handle=content.share_of.author.handle,
            created_at=content.effective_modified,
            public=True if content.visibility == Visibility.PUBLIC else False,
            provider_display_name="Socialhome",
        )
    except Exception as ex:
        logger.exception("_make_share - Failed to convert %s: %s", content.guid, ex)


def get_profile(**kwargs) -> base.Profile:
    """
    Get federable profile from local profile
    """
    from socialhome.users.models import Profile  # Circulars
    kwargs.pop('request', None)
    profile = Profile.objects.select_related('user').get(**kwargs)
    return make_federable_profile(profile)


def make_federable_content(content):
    """Make Content federable by converting it to a federation entity."""
    logger.info("make_federable_content - Content: %s", content)
    if content.content_type == ContentType.REPLY:
        return _make_comment(content)
    elif content.content_type == ContentType.SHARE:
        return _make_share(content)
    return _make_post(content)


def make_federable_retraction(obj, author=None):
    """Make object retraction federable by converting it to a federation entity."""
    logger.info("make_federable_retraction - Object: %s", obj)
    try:
        if isinstance(obj, Content):
            entity_type = {
                ContentType.REPLY: "Comment",
                ContentType.SHARE: "Share",
                ContentType.CONTENT: "Post",
            }.get(obj.content_type)
            handle = author.handle
        elif isinstance(obj, Profile):
            entity_type = "Profile"
            handle = obj.handle
        else:
            logger.warning("make_federable_retraction - Unknown object type %s", obj)
            return
        return base.Retraction(
            entity_type=entity_type,
            handle=handle,
            target_guid=obj.guid,
        )
    except Exception as ex:
        logger.exception("make_federable_retraction - Failed to convert %s: %s", obj.guid, ex)


def make_federable_profile(profile):
    """Make a federable profile."""
    logger.info("make_federable_profile - Profile: %s", profile)
    try:
        return base.Profile(
            handle=profile.handle,
            raw_content="",
            public=True if profile.visibility == Visibility.PUBLIC else False,
            guid=profile.guid,
            name=profile.name,
            image_urls={
                "small": profile.safer_image_url_small,
                "medium": profile.safer_image_url_medium,
                "large": profile.safer_image_url_large,
            },
            public_key=profile.rsa_public_key,
            url=profile.url,
            created_at=profile.created,
            base_url=settings.SOCIALHOME_URL,
            username=profile.user.username if profile.user else "",
        )
    except Exception as ex:
        logger.exception("_make_profile - Failed to convert %s: %s", profile.guid, ex)
        return None
