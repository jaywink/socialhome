import logging

import django_rq
from federation.entities import base
from federation.fetchers import retrieve_remote_profile

from socialhome.content.models import Content
from socialhome.content.utils import safe_text, safe_text_for_markdown
from socialhome.enums import Visibility
from socialhome.federate.utils.generic import safe_make_aware
from socialhome.users.models import Profile

logger = logging.getLogger("socialhome")


def get_sender_profile(sender):
    """Get or create sender profile.

    Fetch it from federation layer if necessary.
    """
    try:
        sender_profile = Profile.objects.get(handle=sender)
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
        logging.info("Entity: %s" % entity)
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
        except Exception as ex:
            logger.exception("Failed to handle %s: %s", entity.guid, ex)


def process_entity_post(entity, profile):
    """Process an entity of type Post."""
    values = {
        "text": safe_text_for_markdown(entity.raw_content),
        "author": profile,
        "visibility": Visibility.PUBLIC if entity.public else Visibility.LIMITED,
        "remote_created": safe_make_aware(entity.created_at, "UTC"),
        "service_label": safe_text(entity.provider_display_name) or "",
    }
    values["text"] = _embed_entity_images_to_post(entity._children, values["text"])
    content, created = Content.objects.update_or_create(guid=safe_text(entity.guid), defaults=values)
    if created:
        logger.info("Saved Content: %s", content)
    else:
        logger.info("Updated Content: %s", content)


def process_entity_comment(entity, profile):
    """Process an entity of type Comment."""
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
    content, created = Content.objects.update_or_create(guid=safe_text(entity.guid), defaults=values)
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


def process_entity_retraction(entity, profile):
    """Process an entity of type Retraction."""
    entity_type = safe_text(entity.entity_type)
    if entity_type != "Post":
        logger.debug("Ignoring retraction of entity_type %s", entity_type)
        return
    target_guid = safe_text(entity.target_guid)
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


def make_federable_entity(content):
    """Make Content federable by converting it to a federation entity."""
    logging.info("make_federable_entity - Content: %s" % content)
    if content.parent:
        return _make_comment(content)
    return _make_post(content)


def make_federable_retraction(content, author):
    """Make Content retraction federable by converting it to a federation entity."""
    logging.info("make_federable_retraction - Content: %s" % content)
    try:
        return base.Retraction(
            entity_type="Post",  # Well, currently, at some point this could be something else
            handle=author.handle,
            target_guid=content.guid,
        )
    except Exception as ex:
        logger.exception("make_federable_retraction - Failed to convert %s: %s", content.guid, ex)
        return None


def sender_key_fetcher(handle):
    """Return the RSA public key for a handle, if found.

    Fetches the key first from a local Profile and if not found, looks for a remote Profile over the network.

    :param handle: Handle of profile
    :type handle: str
    :returns: RSA public key or None
    :rtype: str
    """
    try:
        profile = Profile.objects.get(handle=handle, user__isnull=True)
    except Profile.DoesNotExist:
        remote_profile = retrieve_remote_profile(handle)
        if not remote_profile:
            logger.warning("Remote profile %s for sender key not found locally or remotely.", handle)
            return None
        # We might as well create the profile locally here since we'll need it again soon
        Profile.from_remote_profile(remote_profile)
        return remote_profile.public_key
    else:
        return profile.rsa_public_key
