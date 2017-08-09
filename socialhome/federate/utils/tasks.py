import logging

import django_rq
from federation.entities import base
from federation.fetchers import retrieve_remote_profile

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
        remote_profile = retrieve_remote_profile(sender)
        if not remote_profile:
            logger.warning("Remote profile %s not found locally or remotely.", sender)
            return
        sender_profile = Profile.from_remote_profile(remote_profile)
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
        except Exception as ex:
            logger.exception("Failed to handle %s: %s", entity.guid, ex)


def process_entity_follow(entity, profile):
    """Process entity of type Follow."""
    from socialhome.notifications.tasks import send_follow_notification
    try:
        user = User.objects.get(profile__handle=entity.target_handle, is_active=True)
    except User.DoesNotExist:
        logger.warning("Could not find local user %s for follow entity %s", entity.target_handle, entity)
        return
    if entity.following:
        profile.following.add(user.profile)
        django_rq.enqueue(send_follow_notification, profile.id, user.profile.id)
        logger.info("Profile %s now follows user %s", profile, user)
    else:
        profile.following.remove(user.profile)
        logger.info("Profile %s has unfollowed user %s", profile, user)


def process_entity_relationship(entity, profile):
    """Process entity of type Relationship."""
    from socialhome.notifications.tasks import send_follow_notification
    if not entity.relationship == "following":
        logger.debug("Ignoring relationship of type %s", entity.relationship)
        return
    try:
        user = User.objects.get(profile__handle=entity.target_handle, is_active=True)
    except User.DoesNotExist:
        logger.warning("Could not find local user %s for relationship entity %s", entity.target_handle, entity)
        return
    profile.following.add(user.profile)
    django_rq.enqueue(send_follow_notification, profile.id, user.profile.id)
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
    if parent.is_local:
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
        content = Content.objects.get(guid=target_guid)
    except Content.DoesNotExist:
        logger.warning("Retracted content %s cannot be found", target_guid)
        return
    if content.is_local:
        logger.warning("Local content %s cannot be retracted by a remote retraction!", content)
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


def _make_post(content):
    try:
        return base.Post(
            raw_content=content.text,
            guid=str(content.guid),
            handle=content.author.handle,
            public=True,
            provider_display_name="Socialhome",
            created_at=content.effective_created,
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
            created_at=content.effective_created,
        )
    except Exception as ex:
        logger.exception("_make_comment - Failed to convert %s: %s", content.guid, ex)
        return None


def make_federable_content(content):
    """Make Content federable by converting it to a federation entity."""
    logger.info("make_federable_content - Content: %s", content)
    if content.parent:
        return _make_comment(content)
    return _make_post(content)


def make_federable_retraction(content, author):
    """Make Content retraction federable by converting it to a federation entity."""
    logger.info("make_federable_retraction - Content: %s", content)
    try:
        return base.Retraction(
            entity_type="Comment" if content.parent else "Post",
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
    try:
        profile = Profile.objects.get(handle=handle, user__isnull=True)
        logger.debug("sender_key_fetcher - Handle %s already exists as a profile", handle)
    except Profile.DoesNotExist:
        logger.debug("sender_key_fetcher - Handle %s was not found, fetching from remote", handle)
        remote_profile = retrieve_remote_profile(handle)
        if not remote_profile:
            logger.warning("Remote profile %s for sender key not found locally or remotely.", handle)
            return None
        # We might as well create the profile locally here since we'll need it again soon
        logger.debug("sender_key_fetcher - Creating %s from remote profile", handle)
        Profile.from_remote_profile(remote_profile)
        return remote_profile.public_key
    else:
        return profile.rsa_public_key
