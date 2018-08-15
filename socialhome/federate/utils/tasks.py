import logging
from typing import Optional

import django_rq
from federation.entities import base
from federation.fetchers import retrieve_remote_profile, retrieve_remote_content

from socialhome.content.models import Content
from socialhome.content.utils import safe_text, safe_text_for_markdown
from socialhome.enums import Visibility
from socialhome.utils import safe_make_aware
from socialhome.users.models import Profile, User

logger = logging.getLogger("socialhome")


def get_sender_profile(sender: str) -> Optional[Profile]:
    """Get or create sender profile.

    Fetch it from federation layer if necessary or if the public key is empty for some reason.
    """
    try:
        sender_profile = Profile.objects.exclude(rsa_public_key="").get(fid=sender)
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


def process_entities(entities, receiving_profile=None):
    """Process a list of entities."""
    for entity in entities:
        logger.info("Entity: %s", entity)
        profile = get_sender_profile(entity.actor_id)
        if not profile:
            logger.warning("No sender profile for entity %s, skipping" % entity)
            continue
        try:
            if isinstance(entity, base.Post):
                process_entity_post(entity, profile, receiving_profile=receiving_profile)
            elif isinstance(entity, base.Retraction):
                process_entity_retraction(entity, profile)
            elif isinstance(entity, base.Comment):
                process_entity_comment(entity, profile, receiving_profile=receiving_profile)
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
        user = User.objects.get(profile__fid=entity.target_id, is_active=True)
    except User.DoesNotExist:
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
        old_content = Content.objects.get(fid=fid)
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


def process_entity_post(entity, profile, receiving_profile=None):
    """Process an entity of type Post."""
    fid = safe_text(entity.id)
    if not validate_against_old_content(fid, entity, profile):
        return
    values = {
        "text": safe_text_for_markdown(entity.raw_content),
        "author": profile,
        "visibility": Visibility.PUBLIC if entity.public else Visibility.LIMITED,
        "remote_created": safe_make_aware(entity.created_at, "UTC"),
        "service_label": safe_text(entity.provider_display_name) or "",
    }
    values["text"] = _embed_entity_images_to_post(entity._children, values["text"])
    content, created = Content.objects.update_or_create(fid=fid, defaults=values)
    _process_mentions(content, entity)
    if created:
        logger.info("Saved Content: %s", content)
    else:
        logger.info("Updated Content: %s", content)
    if content.visibility != Visibility.PUBLIC and receiving_profile:
        content.limited_visibilities.add(receiving_profile)
        logger.info("Added visibility to Post %s to %s", content.fid, receiving_profile.fid)


def process_entity_comment(entity, profile, receiving_profile=None):
    """Process an entity of type Comment."""
    fid = safe_text(entity.id)
    if not validate_against_old_content(fid, entity, profile):
        return
    try:
        parent = Content.objects.get(fid=entity.target_id)
    except Content.DoesNotExist:
        logger.warning("No target found for comment: %s", entity)
        return
    values = {
        "text": safe_text_for_markdown(entity.raw_content),
        "author": profile,
        "visibility": parent.visibility,
        "remote_created": safe_make_aware(entity.created_at, "UTC"),
        "parent": parent,
    }
    values["text"] = _embed_entity_images_to_post(entity._children, values["text"])
    content, created = Content.objects.update_or_create(fid=fid, defaults=values)
    _process_mentions(content, entity)
    if created:
        logger.info("Saved Content from comment entity: %s", content)
    else:
        logger.info("Updated Content from comment entity: %s", content)
    if parent.visibility != Visibility.PUBLIC and receiving_profile:
        content.limited_visibilities.add(receiving_profile)
        logger.info("Added visibility to Comment %s to %s", content.uuid, receiving_profile.uuid)
    if parent.local:
        # We should relay this to participants we know of
        from socialhome.federate.tasks import forward_entity
        django_rq.enqueue(forward_entity, entity, parent.id)


def _embed_entity_images_to_post(children, text):
    """Embed any entity `_children` of base.Image type to the text content as markdown.

    Images are prefixed on top of the normal text content.

    :param children: List of child entities
    :param values: Text for creating the Post
    :return: New text value to create the Post with
    """
    images = []
    for child in children:
        if isinstance(child, base.Image):
            image_url = "%s%s" % (
                safe_text(child.remote_path), safe_text(child.remote_name)
            )
            images.append("![](%s) " % image_url)
    if images:
        return "%s\n\n%s" % (
            "".join(images), text
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
            content.mentions.remove(Profile.objects.get(fid=fid))
        except Profile.DoesNotExist:
            pass
    for fid in to_add:
        try:
            content.mentions.add(Profile.objects.get(fid=fid))
        except Profile.DoesNotExist:
            pass


def _retract_content(target_fid, profile):
    """Retract a Content."""
    try:
        content = Content.objects.get(fid=target_fid, local=False)
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
    if entity_type in ("Post", "Comment", "Share"):
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
        target_content = Content.objects.get(fid=entity.target_id, share_of__isnull=True)
    except Content.DoesNotExist:
        # Try fetching. If found, process and then try again
        remote_target = retrieve_remote_content(entity.target_id, sender_key_fetcher=sender_key_fetcher)
        if remote_target:
            process_entities([remote_target])
            try:
                target_content = Content.objects.get(fid=entity.target_id, share_of__isnull=True)
            except Content.DoesNotExist:
                logger.warning("Share target was fetched from remote, but it is still missing locally! Share: %s",
                               entity)
                return
        else:
            logger.warning("No target found for share even after fetching from remote: %s", entity)
            return
    values = {
        "text": safe_text_for_markdown(entity.raw_content),
        "author": profile,
        # TODO: ensure visibility constraints depending on shared content?
        "visibility": Visibility.PUBLIC if entity.public else Visibility.LIMITED,
        "remote_created": safe_make_aware(entity.created_at, "UTC"),
        "service_label": safe_text(entity.provider_display_name) or "",
    }
    values["text"] = _embed_entity_images_to_post(entity._children, values["text"])
    fid = safe_text(entity.id)
    content, created = Content.objects.update_or_create(fid=fid, share_of=target_content, defaults=values)
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
