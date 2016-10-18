import logging

from federation.entities import base
from federation.fetchers import retrieve_remote_profile

from socialhome.content.models import Content
from socialhome.content.utils import safe_text, safe_text_for_markdown_code
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
            logger.warning("Remote profile not found locally or remotely.")
            return
        sender_profile = Profile.objects.create(
            name=safe_text(remote_profile.name),
            guid=safe_text(remote_profile.guid),
            handle=remote_profile.handle,
            visibility=Visibility.PUBLIC if remote_profile.public else Visibility.LIMITED,
            rsa_public_key=safe_text(remote_profile.public_key),
            image_url_large=safe_text(remote_profile.image_urls["large"]),
            image_url_medium=safe_text(remote_profile.image_urls["medium"]),
            image_url_small=safe_text(remote_profile.image_urls["small"]),
            location=safe_text(remote_profile.location),
            email=remote_profile.email,
        )
    return sender_profile


def process_entities(entities, profile):
    """Process a list of entities."""
    for entity in entities:
        logging.info("Entity: %s" % entity)
        if isinstance(entity, base.Post):
            try:
                values = {
                    "text": safe_text_for_markdown_code(entity.raw_content), "author": profile,
                    "visibility": Visibility.PUBLIC if entity.public else Visibility.LIMITED,
                    "remote_created": safe_make_aware(entity.created_at, "UTC"),
                    "service_label": safe_text(entity.provider_display_name) or "",
                }
                content, created = Content.objects.update_or_create(guid=safe_text(entity.guid), defaults=values)
                if created:
                    logger.info("Saved Content: %s", content)
                else:
                    logger.info("Updated Content: %s", content)
            except Exception as ex:
                logger.exception("Failed to handle %s: %s", entity.guid, ex)


def make_federable_entity(content):
    """Make Content federable by converting it to a federation entity."""
    logging.info("make_federable_entity - Content: %s" % content)
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
        logger.exception("make_federable_entity - Failed to convert %s: %s", content.guid, ex)
        return None


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
