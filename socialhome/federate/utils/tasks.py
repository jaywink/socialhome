import logging

import django_rq
from federation.entities import base
from federation.fetchers import retrieve_remote_profile, retrieve_remote_content

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.content.utils import safe_text, safe_text_for_markdown
from socialhome.enums import Visibility
from socialhome.federate.utils.generic import safe_make_aware
from socialhome.users.models import Profile, User

logger = logging.getLogger("socialhome")


def get_sender_profile(sender):
    """Get or create sender profile.

    Fetch it from federation layer if necessary or if the public key is empty for some reason.
    """
    try:
        sender_profile = Profile.objects.exclude(rsa_public_key="").get(handle=sender)
    except Profile.DoesNotExist:
        logger.debug("get_sender_profile - Handle %s was not found, fetching from remote", sender)
        remote_profile = retrieve_remote_profile(sender)
        if not remote_profile:
            logger.warning("get_sender_profile - Remote profile %s not found locally or remotely.", sender)
            return
        sender_profile = Profile.from_remote_profile(remote_profile)
    else:
        if sender_profile.is_local:
            logger.warning("get_sender_profile - Handle %s is local! Skip.", sender)
            return
    return sender_profile


def process_entities(entities):
    """Process a list of entities."""
    for entity in entities:
        logger.info("Entity: %s", entity)
        profile = get_sender_profile(entity.handle)
        if not profile:
            logger.warning("No sender profile for entity %s, skipping" % entity)
            continue
        try:
            if isinstance(entity, base.Post):
                process_entity_post(entity, profile)
            elif isinstance(entity, base.Retraction):
                process_entity_retraction(entity, profile)
            elif isinstance(entity, base.Comment):
                process_entity_comment(entity, profile)
            elif isinstance(entity, base.Relationship):
                process_entity_relationship(entity, profile)
            elif isinstance(entity, base.Follow):
                process_entity_follow(entity, profile)
            elif isinstance(entity, base.Profile):
                Profile.from_remote_profile(entity)
            elif isinstance(entity, base.Share):
                process_entity_share(entity, profile)
        except Exception as ex:
            logger.exception("Failed to handle %s: %s", entity.guid, ex)


def process_entity_follow(entity, profile):
    """Process entity of type Follow."""
    try:
        user = User.objects.get(profile__handle=entity.target_handle, is_active=True)
    except User.DoesNotExist:
        logger.warning("Could not find local user %s for follow entity %s", entity.target_handle, entity)
        return
    if entity.following:
        profile.following.add(user.profile)
        logger.info("Profile %s now follows user %s", profile, user)
    else:
        profile.following.remove(user.profile)
        logger.info("Profile %s has unfollowed user %s", profile, user)


def process_entity_relationship(entity, profile):
    """Process entity of type Relationship."""
    if not entity.relationship == "following":
        logger.debug("Ignoring relationship of type %s", entity.relationship)
        return
    try:
        user = User.objects.get(profile__handle=entity.target_handle, is_active=True)
    except User.DoesNotExist:
        logger.warning("Could not find local user %s for relationship entity %s", entity.target_handle, entity)
        return
    profile.following.add(user.profile)
    logger.info("Profile %s now follows user %s", profile, user)


def validate_against_old_content(guid, entity, profile):
    """Do some validation against a possible local object."""
    try:
        old_content = Content.objects.get(guid=guid)
    except Content.DoesNotExist:
        return True
    # Do some validation
    if old_content.author.user:
        logger.warning("Remote sent update for content (%s) that is local (%s)! Skipping.",
                       guid, old_content.author.handle)
        return False
    if old_content.author != profile:
        logger.warning("Remote sent update for content (%s) with different author (%s) than our content (%s)! "
                       "Skipping.", guid, profile.handle, old_content.author.handle)
        return False
    if old_content.parent and entity.target_guid and old_content.parent.guid != entity.target_guid:
        logger.warning("Remote sent update for content (%s) with different parent! Skipping.", guid)
        return False
    return True


def process_entity_post(entity, profile):
    """Process an entity of type Post."""
    guid = safe_text(entity.guid)
    if not validate_against_old_content(guid, entity, profile):
        return
    values = {
        "text": safe_text_for_markdown(entity.raw_content),
        "author": profile,
        "visibility": Visibility.PUBLIC if entity.public else Visibility.LIMITED,
        "remote_created": safe_make_aware(entity.created_at, "UTC"),
        "service_label": safe_text(entity.provider_display_name) or "",
    }
    values["text"] = _embed_entity_images_to_post(entity._children, values["text"])
    content, created = Content.objects.update_or_create(guid=guid, defaults=values)
    if created:
        logger.info("Saved Content: %s", content)
    else:
        logger.info("Updated Content: %s", content)


def process_entity_comment(entity, profile):
    """Process an entity of type Comment."""
    guid = safe_text(entity.guid)
    if not validate_against_old_content(guid, entity, profile):
        return
    try:
        parent = Content.objects.get(guid=entity.target_guid)
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
    content, created = Content.objects.update_or_create(guid=guid, defaults=values)
    if created:
        logger.info("Saved Content from comment entity: %s", content)
    else:
        logger.info("Updated Content from comment entity: %s", content)
    if parent.local:
        # We should relay this to participants we know of
        from socialhome.federate.tasks import forward_relayable
        django_rq.enqueue(forward_relayable, entity, parent.id)


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


def _retract_content(target_guid, profile):
    """Retract a Content."""
    try:
        content = Content.objects.get(guid=target_guid, local=False)
    except Content.DoesNotExist:
        logger.warning("Retracted remote content %s cannot be found", target_guid)
        return
    if content.author != profile:
        logger.warning("Content %s is not owned by remote retraction profile %s", content, profile)
        return
    # Ok to process retraction
    content.delete()
    logger.info("Retraction done for content %s", content)


def _retract_relationship(target_guid, profile):
    """Retract a (legacy) relationship."""
    try:
        user = User.objects.get(profile__guid=target_guid)
    except User.DoesNotExist:
        logger.warning("Could not find local user %s for relationship retraction", target_guid)
        return
    profile.following.remove(user.profile)
    logger.info("Profile %s has unfollowed user %s", profile, user)


def process_entity_retraction(entity, profile):
    """Process an entity of type Retraction."""
    entity_type = safe_text(entity.entity_type)
    if entity_type == "Post":
        target_guid = safe_text(entity.target_guid)
        _retract_content(target_guid, profile)
    elif entity_type == "Profile":
        # This is legacy stuff and means basically retract sharing/following
        target_guid = safe_text(entity._receiving_guid)
        _retract_relationship(target_guid, profile)
    else:
        logger.debug("Ignoring retraction of entity_type %s", entity_type)


def process_entity_share(entity, profile):
    """Process an entity of type Share."""
    if not entity.entity_type == "Post":
        # TODO: enable shares of replies too
        logger.warning("Ignoring share entity type that is not of type Post")
        return
    try:
        target_content = Content.objects.get(guid=entity.target_guid, share_of__isnull=True)
    except Content.DoesNotExist:
        # Try fetching. If found, process and then try again
        remote_target = retrieve_remote_content(entity.target_id, sender_key_fetcher=sender_key_fetcher)
        if remote_target:
            process_entities([remote_target])
            try:
                target_content = Content.objects.get(guid=entity.target_guid, share_of__isnull=True)
            except Content.DoesNotExist:
                logger.warning("Share target was fetched from remote, but it is still missing locally! Share: %s",
                               entity)
                return
        else:
            logger.warning("No target found for share even after fetching from remote: %s", entity)
            return
    if not target_content.author.handle == entity.target_handle:
        logger.warning("Share target handle is different from the author of locally known shared content!")
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
    guid = safe_text(entity.guid)
    content, created = Content.objects.update_or_create(guid=guid, share_of=target_content, defaults=values)
    if created:
        logger.info("Saved share: %s", content)
    else:
        logger.info("Updated share: %s", content)
    # TODO: send participation to the share from the author, if local
    # We probably want that to happen even though our shares are not separate in the stream?


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


def make_federable_content(content):
    """Make Content federable by converting it to a federation entity."""
    logger.info("make_federable_content - Content: %s", content)
    if content.content_type == ContentType.REPLY:
        return _make_comment(content)
    elif content.content_type == ContentType.SHARE:
        return _make_share(content)
    return _make_post(content)


def make_federable_retraction(content, author):
    """Make Content retraction federable by converting it to a federation entity."""
    logger.info("make_federable_retraction - Content: %s", content)
    try:
        entity_type = "Comment" if content.content_type == ContentType.REPLY else \
            "Share" if content.content_type == ContentType.SHARE else "Post"
        return base.Retraction(
            # TODO check share federation
            entity_type=entity_type,
            handle=author.handle,
            target_guid=content.guid,
        )
    except Exception as ex:
        logger.exception("make_federable_retraction - Failed to convert %s: %s", content.guid, ex)
        return None


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
        )
    except Exception as ex:
        logger.exception("_make_profile - Failed to convert %s: %s", profile.guid, ex)
        return None


def sender_key_fetcher(handle):
    """Return the RSA public key for a handle, if found.

    Fetches the key first from a local Profile and if not found, looks for a remote Profile over the network.

    :param handle: Handle of profile
    :type handle: str
    :returns: RSA public key or None
    :rtype: str
    """
    logger.debug("sender_key_fetcher - Checking for handle '%s'", handle)
    profile = get_sender_profile(handle)
    if not profile:
        return
    return profile.rsa_public_key
