import logging
from typing import Optional, Union

from django.conf import settings
from federation.entities import base

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.enums import Visibility
from socialhome.users.models import Profile

logger = logging.getLogger("socialhome")


def _make_post(content: Content) -> Optional[base.Post]:
    try:
        return base.Post(
            raw_content=content.text,
            id=content.fid,
            actor_id=content.author.fid,
            public=True if content.visibility == Visibility.PUBLIC else False,
            provider_display_name="Socialhome",
            created_at=content.effective_modified,
        )
    except Exception as ex:
        logger.exception("_make_post - Failed to convert %s: %s", content.fid, ex)


def _make_comment(content: Content) -> Optional[base.Comment]:
    try:
        return base.Comment(
            raw_content=content.text,
            id=content.fid,
            actor_id=content.author.fid,
            target_id=content.parent.fid,
            created_at=content.effective_modified,
        )
    except Exception as ex:
        logger.exception("_make_comment - Failed to convert %s: %s", content.fid, ex)


def _make_share(content: Content) -> Optional[base.Share]:
    try:
        return base.Share(
            raw_content=content.text,
            id=content.fid,
            target_id=content.share_of.fid,
            actor_id=content.author.fid,
            created_at=content.effective_modified,
            public=True if content.visibility == Visibility.PUBLIC else False,
            provider_display_name="Socialhome",
        )
    except Exception as ex:
        logger.exception("_make_share - Failed to convert %s: %s", content.fid, ex)


def get_profile(**kwargs) -> base.Profile:
    """
    Get federable profile from local profile
    """
    from socialhome.users.models import Profile  # Circulars
    kwargs.pop('request', None)
    profile = Profile.objects.select_related('user').get(**kwargs)
    return make_federable_profile(profile)


def make_federable_content(content: Content) -> Optional[Union[base.Post, base.Comment, base.Share]]:
    """Make Content federable by converting it to a federation entity."""
    logger.info("make_federable_content - Content: %s", content)
    if content.content_type == ContentType.REPLY:
        return _make_comment(content)
    elif content.content_type == ContentType.SHARE:
        return _make_share(content)
    return _make_post(content)


def make_federable_retraction(obj: Union[Content, Profile], author: Optional[Profile]=None):
    """Make object retraction federable by converting it to a federation entity."""
    logger.info("make_federable_retraction - Object: %s", obj)
    try:
        if isinstance(obj, Content):
            entity_type = {
                ContentType.REPLY: "Comment",
                ContentType.SHARE: "Share",
                ContentType.CONTENT: "Post",
            }.get(obj.content_type)
            actor_id = author.fid
        elif isinstance(obj, Profile):
            entity_type = "Profile"
            actor_id=obj.fid
        else:
            logger.warning("make_federable_retraction - Unknown object type %s", obj)
            return
        return base.Retraction(
            entity_type=entity_type,
            actor_id=actor_id,
            target_id=obj.fid,
        )
    except Exception as ex:
        logger.exception("make_federable_retraction - Failed to convert %s: %s", obj.fid, ex)


def make_federable_profile(profile):
    """Make a federable profile."""
    logger.info("make_federable_profile - Profile: %s", profile)
    try:
        return base.Profile(
            raw_content="",
            public=True if profile.visibility == Visibility.PUBLIC else False,
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
            id=profile.fid,
        )
    except Exception as ex:
        logger.exception("_make_profile - Failed to convert %s: %s", profile.uuid, ex)
        return None
