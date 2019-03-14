import logging
from typing import Optional, Union

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from federation.entities import base
from federation.entities.mixins import BaseEntity

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
            guid=str(content.uuid),
            handle=content.author.handle,
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
            guid=str(content.uuid),
            handle=content.author.handle,
            target_guid=content.parent.guid,
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
            guid=str(content.uuid),
            handle=content.author.handle,
            target_guid=content.share_of.guid,
            target_handle=content.share_of.author.handle,
        )
    except Exception as ex:
        logger.exception("_make_share - Failed to convert %s: %s", content.fid, ex)


def get_federable_object(request: HttpRequest) -> Optional[BaseEntity]:
    """
    Retrieve local object and return it as a federable version.

    Ensure to check permissions before returning object.
    """
    object_id = request.build_absolute_uri()
    user = getattr(request, 'user', AnonymousUser())
    if request.path.startswith('/content/'):
        content = Content.objects.filter(fid=object_id).first()
        if content and content.visible_for_user(user):
            federable_content = make_federable_content(content)
            return federable_content
    elif request.path.startswith('/p/') or request.path == '/':
        if settings.SOCIALHOME_ROOT_PROFILE and object_id.rstrip('/') == settings.SOCIALHOME_URL.rstrip('/'):
            profile = Profile.objects.get(user__username=settings.SOCIALHOME_ROOT_PROFILE)
        else:
            profile = Profile.objects.filter(fid=object_id).first()
        if profile and profile.visible_to_user(user):
            federable_profile = make_federable_profile(profile)
            return federable_profile


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
            handle = author.handle
        elif isinstance(obj, Profile):
            entity_type = "Profile"
            actor_id = obj.fid
            handle = obj.handle
        else:
            logger.warning("make_federable_retraction - Unknown object type %s", obj)
            return
        return base.Retraction(
            entity_type=entity_type,
            actor_id=actor_id,
            target_id=obj.fid,
            handle=handle,
            target_guid=obj.guid,
        )
    except Exception as ex:
        logger.exception("make_federable_retraction - Failed to convert %s: %s", obj.fid, ex)


def make_federable_profile(profile: Profile) -> Optional[base.Profile]:
    """Make a federable profile."""
    logger.info("make_federable_profile - Profile: %s", profile)
    if not profile.is_local:
        return
    try:
        return base.Profile(
            raw_content="",
            public=True,  # A profile is public in the context of federation if it is sent outwards
            name=profile.name,
            image_urls={
                "small": profile.safer_image_url_small,
                "medium": profile.safer_image_url_medium,
                "large": profile.safer_image_url_large,
            },
            public_key=profile.rsa_public_key,
            url=profile.local_url,
            created_at=profile.created,
            base_url=settings.SOCIALHOME_URL,
            id=profile.fid,
            handle=profile.handle or "",
            guid=str(profile.uuid),
        )
    except Exception as ex:
        logger.exception("_make_profile - Failed to convert %s: %s", profile.uuid, ex)
        return
