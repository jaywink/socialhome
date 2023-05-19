import logging
import re
from typing import Optional, Union, List, Dict, Tuple

from Crypto.PublicKey.RSA import RsaKey
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db.models.query_utils import Q
from django.db.utils import ProgrammingError
from django.http import HttpRequest
from federation.entities import base
from federation.entities.activitypub.constants import NAMESPACE_PUBLIC
from federation.entities.mixins import BaseEntity
from federation.types import UserType, ReceiverVariant

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
            times = {'created':content.created, 'modified':content.modified, 'edited':content.edited},
            guid=str(content.uuid),
            handle=content.author.handle,
            mxid=content.author.mxid,
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
            root_target_id=content.root_parent.fid,
            created_at=content.effective_modified,
            times = {'created':content.created, 'modified':content.modified, 'edited':content.edited},
            guid=str(content.uuid),
            handle=content.author.handle,
            target_guid=content.parent.guid,
            root_target_guid=content.root_parent.guid,
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


def get_federable_object(request: HttpRequest, signer: str = None) -> Optional[BaseEntity]:
    """
    Retrieve local object and return it as a federable version.

    Ensure to check permissions before returning object.

    The signer is extracted and validated from the request signature header.
    """
    object_id = request.build_absolute_uri()
    user = getattr(request, 'user', AnonymousUser())
    if request.path.startswith('/content/'):
        content = Content.objects.filter(fid=object_id).first()
        if content and content.author.is_local and (
                content.visible_for_user(user) or content.visible_for_fed_user(signer)):
            federable_content = make_federable_content(content)
            return federable_content
    elif request.path.startswith('/u/') or request.path == '/':
        if settings.SOCIALHOME_ROOT_PROFILE and object_id.rstrip('/') == settings.SOCIALHOME_URL.rstrip('/'):
            profile = Profile.objects.get(user__username=settings.SOCIALHOME_ROOT_PROFILE)
        else:
            profile = Profile.objects.filter(fid=object_id).first()
        if profile and profile.visible_to_user(user):
            federable_profile = make_federable_profile(profile)
            return federable_profile
        else:
            return _make_federable_collection(object_id, request.path, user)


def _make_federable_collection(fid, path, user):
    """
    WIP: Provide a response for some AP collection requests
    Should this be done using views?
    TODO: implement collection pages
    """
    try:
        coll = re.match(r'.+/(\w+)/$', path).groups()[0]
    except AttributeError:
        return None
    if coll in ('followers', 'following', 'outbox', 'featured'):
        fid = fid.replace(coll+'/', '')
    else:
        return None

    profile = Profile.objects.filter(fid=fid).first()
    if profile and profile.is_local and profile.visible_to_user(user):
        if coll in ('followers', 'following'):
            # return item count only until pages are implemented
            return base.Collection(
                id = profile.fid+coll+'/',
                #items = list(getattr(profile,coll).filter(fid__isnull=False).values_list('fid',flat=True)),
                total_items = getattr(profile,coll).filter(fid__isnull=False).count(),
                ordered = True,
                )
        elif coll in ('outbox', 'featured'):
            # unimplemnted
            return None


def get_profile(**kwargs) -> base.Profile:
    """
    Get federable profile from local profile
    """
    from socialhome.users.models import Profile  # Circulars
    kwargs.pop('request', None)
    profile = Profile.objects.select_related('user').get(**kwargs)
    return make_federable_profile(profile)


def get_receivers_for_content(content: Content) -> Tuple:
    """
    Return values are used by federation to populate AP to and cc fields
    """
    to = []
    cc = []

    mentions = content.mentions.filter(fid__isnull=False).values_list("fid", flat=True)
    followers = content.author.fid + 'followers/'

    if content.content_type == ContentType.SHARE:
        to = [NAMESPACE_PUBLIC]
        cc = [content.share_of.author.fid, followers]
    elif content.visibility == Visibility.PUBLIC:
        to = [NAMESPACE_PUBLIC]
        cc = list(mentions) + [followers]
    elif content.visibility == Visibility.LIMITED:
        to = list(mentions)
        if content.include_following:
            if to: cc = [followers]
            else: to = [followers]

    return to, cc

def get_profiles_from_receivers(receivers: List[UserType]) -> List[Profile]:
    """
    Get a list of local Profile objects from a list of receivers in an entity.
    """
    profile_ids = set()
    for receiver in receivers:
        if receiver.receiver_variant == ReceiverVariant.ACTOR:
            try:
                profile = Profile.objects.fed(receiver.id, user__isnull=False).get()
            except Profile.DoesNotExist:
                continue
            else:
                profile_ids.add(profile.id)
        elif receiver.receiver_variant == ReceiverVariant.FOLLOWERS:
            sender = Profile.objects.fed(receiver.id, user__isnull=True)
            receiver_ids = set(
                Profile.objects.filter(user__isnull=False, following__in=sender).values_list("id", flat=True),
            )
            profile_ids = profile_ids.union(receiver_ids)
    return Profile.objects.filter(id__in=profile_ids)


def get_user_private_key(identifier: str) -> Optional[RsaKey]:
    """
    Get a local user private key by identifier (fid, handle or guid).
    """
    if not identifier: return
    from socialhome.users.models import Profile  # Circulars
    try:
        profile = Profile.objects.only('rsa_private_key').get(
            Q(fid=identifier) | Q(handle=identifier) | Q(guid=identifier),
        )
    except Profile.DoesNotExist:
        logger.error('get_user_private_key - no profile for %s' % identifier)
        return
    except ProgrammingError:
        return
    return profile.private_key


def make_federable_content(content: Content) -> Optional[Union[base.Post, base.Comment, base.Share]]:
    """Make Content federable by converting it to a federation entity."""
    logger.info("make_federable_content - Content: %s", content)
    if content.content_type == ContentType.REPLY:
        ret = _make_comment(content)
    elif content.content_type == ContentType.SHARE:
        ret = _make_share(content)
    else: ret = _make_post(content)
    if content.author.fid and isinstance(content.author.fid, str):
        ret.to, ret.cc = get_receivers_for_content(content)
    return ret



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
            if obj.content_type == ContentType.SHARE:
                target_id = obj.share_of.fid
            else:
                target_id = obj.fid
        elif isinstance(obj, Profile):
            entity_type = "Profile"
            actor_id = obj.fid
            handle = obj.handle
            target_id = obj.fid
        else:
            logger.warning("make_federable_retraction - Unknown object type %s", obj)
            return
        ret = base.Retraction(
            id=obj.activities.first().fid,
            entity_type=entity_type,
            actor_id=actor_id,
            target_id=target_id,
            handle=handle,
            target_guid=obj.guid,
            created_at=obj.effective_modified,
        )
        if obj.author.fid and isinstance(obj.author.fid, str):
            ret.to, ret.cc = get_receivers_for_content(obj)
        return ret
    except Exception as ex:
        logger.exception("make_federable_retraction - Failed to convert %s: %s", obj.fid, ex)


def make_federable_profile(profile: Profile) -> Optional[base.Profile]:
    """Make a federable profile."""
    logger.info("make_federable_profile - Profile: %s", profile)
    try:
        return base.Profile(
            raw_content="",
            public=True,  # A profile is public in the context of federation if it is sent outwards
            name=profile.name_or_handle,
            image_urls={
                "small": profile.safer_image_url_small,
                "medium": profile.safer_image_url_medium,
                "large": profile.safer_image_url_large,
            },
            public_key=profile.rsa_public_key,
            url=profile.url,
            created_at=profile.created,
            times={
                'created': profile.created,
                'updated': profile.modified,
                'edited': False,
            },
            base_url=settings.SOCIALHOME_URL,
            id=profile.fid,
            handle=profile.handle or "",
            finger=profile.finger or "",
            guid=str(profile.uuid) if profile.is_local else profile.guid if profile.guid else "",
            inboxes={
                "private": profile.inbox_private,
                "public": profile.inbox_public,
            },
            username=profile.username_part,
            mxid=profile.mxid or "",
        )
    except Exception as ex:
        logger.exception("_make_profile - Failed to convert %s: %s", profile.uuid, ex)
        return
