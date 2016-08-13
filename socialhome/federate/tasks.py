# -*- coding: utf-8 -*-
import logging

from federation.entities import base
from federation.fetchers import retrieve_remote_profile
from federation.inbound import handle_receive
from federation.exceptions import NoSuitableProtocolFoundError

from socialhome.content.models import Content
from socialhome.content.utils import safe_text_for_markdown_code, safe_text
from socialhome.enums import Visibility
from socialhome.federate.utils import safe_make_aware
from socialhome.taskapp.celery import tasks
from socialhome.users.models import Profile

logger = logging.getLogger("socialhome")


@tasks.task()
def receive_task(payload, guid=None):
    """Process received payload."""
    # TODO: we're skipping author verification until fetching of remote profile public keys is implemented
    profile = None
    if guid:
        try:
            profile = Profile.objects.get(guid=guid, user__isnull=False)
        except Profile.DoesNotExist:
            logger.warning("No local profile found with guid")
            return
    try:
        sender, protocol_name, entities = handle_receive(payload, user=profile, skip_author_verification=True)
        logger.debug("sender=%s, protocol_name=%s, entities=%s" % (sender, protocol_name, entities))
    except NoSuitableProtocolFoundError:
        logger.warning("No suitable protocol found for payload")
        return
    if not entities:
        logger.warning("No entities in payload")
        return
    sender_profile = get_sender_profile(sender)
    if not sender_profile:
        return
    process_entities(entities, profile=sender_profile)


def get_sender_profile(sender):
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
                    logger.info("Saved Content: %s" % content)
                else:
                    logger.info("Updated Content: %s" % content)
            except Exception as ex:
                logger.exception("Failed to handle %s: %s" % (entity.guid, ex))
