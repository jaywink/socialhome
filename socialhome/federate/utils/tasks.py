import logging
import datetime as dt
from typing import Optional, List, Any

import django_rq
from federation.entities import base
from federation.fetchers import retrieve_remote_profile, retrieve_remote_content

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.content.utils import safe_text, safe_text_for_markdown
from socialhome.enums import Visibility
from socialhome.federate.utils import get_profiles_from_receivers
from socialhome.utils import safe_make_aware
from socialhome.users.models import Profile, User

logger = logging.getLogger("socialhome")


def get_sender_profile(sender: str) -> Optional[Profile]:
    """Get or create sender profile.

    Fetch it from federation layer if necessary or if the public key is empty for some reason.
    """
    try:
        logger.debug("get_sender_profile - looking from local db using %s", sender)
        sender_profile = Profile.objects.fed(sender).exclude(rsa_public_key="").get()
    except Profile.DoesNotExist:
        logger.debug("get_sender_profile - %s was not found, fetching from remote", sender)
        remote_profile = retrieve_remote_profile(sender)
        if not remote_profile:
            logger.warning("get_sender_profile - Remote profile %s not found locally or remotely.", sender)
            return
        sender_profile = Profile.from_remote_profile(remote_profile)
    else:
        if sender_profile.is_local:
            logger.warning("get_sender_profile - %s is local! Skip.", sender)
            return
    return sender_profile


def process_entities(entities: List):
    """Process a list of entities."""
    for entity in entities:
        logger.info("Entity: %s", entity)
        # noinspection PyProtectedMember
        logger.info("Receivers: %s", entity._receivers)
        sender_id = entity.id if isinstance(entity, base.Profile) else entity.actor_id
        profile = get_sender_profile(sender_id)
        if not profile:
            logger.warning("No sender profile for entity %s, skipping", entity)
            continue
        try:
            if isinstance(entity, base.Post):
                process_entity_post(entity, profile)
            elif isinstance(entity, base.Retraction):
                process_entity_retraction(entity, profile)
            elif isinstance(entity, base.Comment):
                process_entity_comment(entity, profile)
            elif isinstance(entity, base.Follow):
                process_entity_follow(entity, profile)
            elif isinstance(entity, base.Profile):
                Profile.from_remote_profile(entity)
            elif isinstance(entity, base.Share):
                process_entity_share(entity, profile)
        except Exception as ex:
            logger.exception("Failed to handle %s: %s", entity.id, ex)


def process_entity_follow(entity, profile):
    """Process entity of type Follow."""
    try:
        user = User.objects.get(profile=Profile.objects.fed(entity.target_id).get(), is_active=True)
    except (Profile.DoesNotExist, User.DoesNotExist):
        logger.warning("Could not find local user %s for follow entity %s", entity.target_id, entity)
        return
    if entity.following:
        profile.following.add(user.profile)
        logger.info("Profile %s now follows user %s", profile, user)
    else:
        profile.following.remove(user.profile)
        logger.info("Profile %s has unfollowed user %s", profile, user)


def validate_against_old_content(fid, entity, profile):
    """Do some validation against a possible local object."""
    try:
        old_content = Content.objects.fed(fid).get()
    except Content.DoesNotExist:
        return True
    # Do some validation
    if old_content.author.user:
        logger.warning("Remote sent update for content (%s) that is local (%s)! Skipping.",
                       fid, old_content.author.fid)
        return False
    if old_content.author != profile:
        logger.warning("Remote sent update for content (%s) with different author (%s) than our content (%s)! "
                       "Skipping.", fid, profile.fid, old_content.author.fid)
        return False
    if old_content.parent and entity.target_id and old_content.parent.fid != entity.target_id:
        logger.warning("Remote sent update for content (%s) with different parent! Skipping.", fid)
        return False
    return True


# noinspection PyProtectedMember
def process_entity_post(entity: Any, profile: Profile):
    """Process an entity of type Post."""
    fid = safe_text(entity.id)
    if not validate_against_old_content(fid, entity, profile):
        return
    values = {
        "fid": fid,
        "text": _embed_entity_medias_to_post(entity._children, safe_text_for_markdown(entity.raw_content)),
        "author": profile,
        "visibility": Visibility.PUBLIC if entity.public else Visibility.LIMITED,
        "remote_created": safe_make_aware(entity.created_at, "UTC"),
        "service_label": safe_text(entity.provider_display_name) or "",
    }
    extra_lookups = {}
    if getattr(entity, "guid", None):
        values["guid"] = safe_text(entity.guid)
        extra_lookups["guid"] = values["guid"]
    content, created = Content.objects.fed_update_or_create(fid, values, extra_lookups=extra_lookups)
    _process_mentions(content, entity)
    if created:
        logger.info("Saved Content: %s", content)
    else:
        logger.info("Updated Content: %s", content)
    if content.visibility == Visibility.LIMITED:
        if entity._receivers:
            receivers = get_profiles_from_receivers(entity._receivers)
            if len(receivers):
                content.limited_visibilities.set(receivers)
                logger.info("Added visibility to Post %s to %s", content.fid, receivers)
            else:
                logger.warning("No local receivers found for limited Post %s", content.fid)
        else:
            logger.warning("No receivers for limited Post %s", content.fid)

    if hasattr(entity, '_replies'):
        if django_rq.get_scheduler().enqueue_in(dt.timedelta(seconds=90), process_replies, entity):
            logger.info("process_replies - queued job for entity %s", entity.id)
        else:
            logger.warn("process_replies - failed to enqueue job for entity %s", entity.id)


# noinspection PyProtectedMember
def process_entity_comment(entity: Any, profile: Profile):
    """Process an entity of type Comment."""
    fid = safe_text(entity.id)
    if not validate_against_old_content(fid, entity, profile):
        return
    try:
        parent = Content.objects.fed(entity.target_id).get()
    except Content.DoesNotExist:
        # Try fetching. If found, process and then try again
        # This maybe useless as federation should walk up to the root
        # and down the reply collection
        logger.debug(
            "process_entity_comment - trying to fetch %s, %s, %s, %s, %s",
            entity.target_id, entity.target_guid, entity.target_handle, entity.entity_type, sender_key_fetcher,
        )
        remote_target = retrieve_remote_content(
            entity.target_id,
            guid=entity.target_guid,
            handle=entity.target_handle,
            entity_type=entity.entity_type,
            sender_key_fetcher=sender_key_fetcher,
        )
        if remote_target:
            process_entities([remote_target])
            try:
                parent = Content.objects.fed(entity.target_id).get()
            except Content.DoesNotExist:
                logger.warning("Comment target was fetched from remote, but it is still missing locally! Comment: %s",
                               entity)
                return
        else:
            logger.warning("No target found for comment even after fetching from remote: %s", entity)
            return
    root_parent = parent
    if entity.root_target_id:
        try:
            root_parent = Content.objects.fed(entity.root_target_id).get()
        except Content.DoesNotExist:
            pass
    visibility = None
    if getattr(entity, "public", None) is not None:
        visibility = Visibility.PUBLIC if entity.public else Visibility.LIMITED
    values = {
        "text": _embed_entity_medias_to_post(entity._children, safe_text_for_markdown(entity.raw_content)),
        "author": profile,
        "visibility": visibility if visibility is not None else parent.visibility,
        "remote_created": safe_make_aware(entity.created_at, "UTC"),
        "parent": parent,
        "root_parent": root_parent,
    }
    extra_lookups = {}
    if getattr(entity, "guid", None):
        values["guid"] = safe_text(entity.guid)
        extra_lookups["guid"] = values["guid"]
    content, created = Content.objects.fed_update_or_create(fid, values, extra_lookups=extra_lookups)
    _process_mentions(content, entity)
    if created:
        logger.info("Saved Content from comment entity: %s", content)
    else:
        logger.info("Updated Content from comment entity: %s", content)

    if visibility == Visibility.LIMITED or (visibility is None and parent.visibility == Visibility.LIMITED):
        if entity._receivers:
            receivers = get_profiles_from_receivers(entity._receivers)
            if len(receivers):
                content.limited_visibilities.add(*receivers)
                logger.info("Added visibility to Comment %s to %s", content.fid, receivers)
            else:
                logger.warning("No local receivers found for limited Comment %s", content.fid)
        else:
            logger.warning("No receivers for limited Comment %s", content.fid)

    if parent.local:
        # We should relay this to participants we know of
        from socialhome.federate.tasks import forward_entity
        django_rq.enqueue(forward_entity, entity, root_parent.id)

    if hasattr(entity, '_replies'):
        if django_rq.get_scheduler().enqueue_in(dt.timedelta(seconds=90), process_replies, entity):
            logger.info("process_replies - queued job for entity %s", entity.id)
        else:
            logger.warn("process_replies - failed to enqueue job for entity %s", entity.id)


def _embed_entity_medias_to_post(children, text):
    """Embed any entity `_children` of base.Image type to the text content as markdown.
    Embed base.[Audio, Video] types to the text content as HTML5

    Medias are suffixed at the bottom of the normal text content.

    :param children: List of child entities
    :param values: Text for creating the Post
    :return: New text value to create the Post with
    """
    medias = []
    for child in children:
        if isinstance(child, base.Image):
            medias.append(f"![{safe_text(child.name)}]({safe_text(child.url)}) ")
        if isinstance(child, base.Audio):
            audio = f'<audio controls><source src="{safe_text(child.url)}" type="{safe_text(child.media_type)}"></audio>'
            if getattr(child, 'name', None):
                audio = f"<p>{safe_text(child.name)}</p>" + audio
            medias.append(audio)
        if isinstance(child, base.Video):
            video = f'<video controls><source src="{safe_text(child.url)}" type="{safe_text(child.media_type)}"></video>'
            if getattr(child, 'name', None):
                video = f"<p>{safe_text(child.name)}</p>" + video
            medias.append(video)

    if medias:
        return "%s\n\n%s" % (
            text, "".join(medias)
        )
    return text


def _process_mentions(content, entity):
    """
    Link mentioned profiles to the content.
    """
    fids = set(entity._mentions)
    existing_fids = set(content.mentions.values_list('fid', flat=True))
    to_remove = existing_fids.difference(fids)
    to_add = fids.difference(existing_fids)
    for fid in to_remove:
        try:
            content.mentions.remove(Profile.objects.fed(fid).get())
        except Profile.DoesNotExist:
            pass
    for fid in to_add:
        try:
            content.mentions.add(Profile.objects.fed(fid).get())
        except Profile.DoesNotExist:
            pass


def _retract_content(target_fid, profile):
    """Retract a Content."""
    try:
        content = Content.objects.fed(target_fid, local=False).get()
    except Content.DoesNotExist:
        # Try by shared activity fid
        try:
            content = Content.objects.get(activities__fid=target_fid, local=False, content_type=ContentType.SHARE)
        except Content.DoesNotExist:
            logger.warning("Retracted remote content %s cannot be found", target_fid)
            return
    if content.author != profile:
        logger.warning("Content %s is not owned by remote retraction profile %s", content, profile)
        return
    # Ok to process retraction
    content.delete()
    logger.info("Retraction done for content %s", content)


def _retract_relationship(target_uuid, profile):
    """Retract a (legacy) relationship."""
    try:
        user = User.objects.get(profile__uuid=target_uuid)
    except User.DoesNotExist:
        logger.warning("Could not find local user %s for relationship retraction", target_uuid)
        return
    profile.following.remove(user.profile)
    logger.info("Profile %s has unfollowed user %s", profile, user)


def process_entity_retraction(entity, profile):
    """Process an entity of type Retraction."""
    entity_type = safe_text(entity.entity_type)
    # TODO: Currently "Object" only tries Content - once we actually have other non-Content retractions - fix this!
    #       It should try all possible retractable objects.
    if entity_type in ("Post", "Comment", "Share", "Object"):
        target_fid = safe_text(entity.target_id)
        _retract_content(target_fid, profile)
    else:
        logger.debug("Ignoring retraction of entity_type %s", entity_type)


def process_entity_share(entity, profile):
    """Process an entity of type Share."""
    if not entity.entity_type == "Post":
        # TODO: enable shares of replies too
        logger.warning("Ignoring share entity type that is not of type Post")
        return
    try:
        target_content = Content.objects.fed(entity.target_id, share_of__isnull=True).get()
    except Content.DoesNotExist:
        # Try fetching. If found, process and then try again
        logger.debug(
            "process_entity_share - trying to fetch %s, %s, %s, %s, %s",
            entity.target_id, entity.target_guid, entity.target_handle, entity.entity_type, sender_key_fetcher,
        )
        remote_target = retrieve_remote_content(
            entity.target_id,
            guid=entity.target_guid,
            handle=entity.target_handle,
            entity_type=entity.entity_type,
            sender_key_fetcher=sender_key_fetcher,
        )
        if remote_target:
            process_entities([remote_target])
            try:
                target_content = Content.objects.fed(entity.target_id, share_of__isnull=True).get()
            except Content.DoesNotExist:
                logger.warning("Share target was fetched from remote, but it is still missing locally! Share: %s",
                               entity)
                return
        else:
            logger.warning("No target found for share even after fetching from remote: %s", entity)
            return
    if target_content.visibility != Visibility.PUBLIC:
        # Don't process a share for non-public target content
        logger.warning("Share '%s' target '%s' is not public - aborting", entity, target_content)
        return
    values = {
        "text": safe_text_for_markdown(entity.raw_content),
        "author": profile,
        "visibility": Visibility.PUBLIC,
        "remote_created": safe_make_aware(entity.created_at, "UTC"),
        "service_label": safe_text(entity.provider_display_name) or "",
    }
    # noinspection PyProtectedMember
    values["text"] = _embed_entity_medias_to_post(entity._children, values["text"])
    fid = safe_text(entity.id)
    if getattr(entity, "guid", None):
        values["guid"] = safe_text(entity.guid)
    content, created = Content.objects.fed_update_or_create(fid, values, extra_lookups={'share_of': target_content})
    _process_mentions(content, entity)
    if created:
        logger.info("Saved share: %s", content)
    else:
        logger.info("Updated share: %s", content)
    # TODO: send participation to the share from the author, if local
    # We probably want that to happen even though our shares are not separate in the stream?
    if target_content.local:
        # We should relay this share entity to participants we know of
        from socialhome.federate.tasks import forward_entity
        django_rq.enqueue(forward_entity, entity, target_content.id)


def process_replies(entity=None, fetch=False, delta=None):
    # Process Activitypub reply collection
    if fetch:
        # Refresh entity
        entity = retrieve_remote_content(entity.id, cache=False)
        if not entity: return


    for reply in getattr(entity, '_replies', []):
        try:
            content = Content.objects.fed(reply).get()
        except Content.DoesNotExist:
            # Try to fetch and process
            logger.debug(
                "process_replies - fetching reply %s for entity %s", reply, entity.id)
            remote_content = retrieve_remote_content(reply)
            if remote_content:
                process_entities([remote_content])
    
    # Using a delta increasing by a factor of two, refresh
    # the replies up to 5 days after publication
    delta = delta * 2 if delta else dt.timedelta(minutes=15)
    if hasattr(entity, '_replies'):
        if delta < dt.timedelta(5):
            if django_rq.get_scheduler().enqueue_in(delta, process_replies, entity, True, delta):
                logger.info("process_replies - queued refresh job for entity %s", entity.id)
            else:
                logger.warn("process_replies - failed to enqueue refresh job for entity %s", entity.id)


def sender_key_fetcher(fid):
    """Return the RSA public key for a fid, if found.

    Fetches the key first from a local Profile and if not found, looks for a remote Profile over the network.

    :param fid: Fid of profile
    :type fid: str
    :returns: RSA public key or None
    :rtype: str
    """
    logger.debug("sender_key_fetcher - Checking for fid '%s'", fid)
    profile = get_sender_profile(fid)
    if not profile:
        return
    return profile.rsa_public_key
