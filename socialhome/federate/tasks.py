import logging

from django.conf import settings
from federation.exceptions import NoSuitableProtocolFoundError, NoSenderKeyFoundError, SignatureVerificationError
from federation.inbound import handle_receive
from federation.outbound import handle_create_payload
from federation.utils.network import send_document
from socialhome.content.models import Content

from socialhome.enums import Visibility
from socialhome.federate.utils.tasks import (
    process_entities, make_federable_entity, make_federable_retraction, sender_key_fetcher
)
from socialhome.users.models import Profile

logger = logging.getLogger("socialhome")


def receive_task(payload, guid=None):
    """Process received payload."""
    profile = None
    if guid:
        try:
            profile = Profile.objects.get(guid=guid, user__isnull=False)
        except Profile.DoesNotExist:
            logger.warning("No local profile found with guid")
            return
    try:
        sender, protocol_name, entities = handle_receive(payload, user=profile, sender_key_fetcher=sender_key_fetcher)
        logger.debug("sender=%s, protocol_name=%s, entities=%s" % (sender, protocol_name, entities))
    except NoSuitableProtocolFoundError:
        logger.warning("No suitable protocol found for payload")
        return
    except NoSenderKeyFoundError:
        logger.warning("Could not find a public key for the sender - skipping payload")
        return
    except SignatureVerificationError:
        logger.warning("Signature validation failed - skipping payload")
        return
    if not entities:
        logger.warning("No entities in payload")
        return
    process_entities(entities)


def send_content(content_id):
    """Handle sending a Content object out via the federation layer.

    Currently we only deliver public content.
    """
    try:
        content = Content.objects.get(id=content_id)
    except Content.DoesNotExist:
        logger.warning("No content found with id %s", content_id)
        return
    if not content.visibility == Visibility.PUBLIC:
        return
    entity = make_federable_entity(content)
    if entity:
        if settings.DEBUG:
            # Don't send in development mode
            return
        # TODO: federation should provide one method to send,
        # which handles also payload creation and url calculation
        payload = handle_create_payload(entity, content.author)
        # Just dump to the relay system for now
        url = "https://%s/receive/public" % settings.SOCIALHOME_RELAY_DOMAIN
        send_document(url, payload)
    else:
        logger.warning("No entity for %s", content)


def send_reply(content_id):
    """Handle sending a Content object that is a reply out via the federation layer.

    Currently we only deliver public content.
    """
    try:
        content = Content.objects.get(id=content_id, visibility=Visibility.PUBLIC)
    except Content.DoesNotExist:
        logger.warning("No content found with id %s", content_id)
        return
    entity = make_federable_entity(content)
    if entity:
        if settings.DEBUG:
            # Don't send in development mode
            return
        # TODO: federation should provide one method to send,
        # which handles also payload creation and url calculation
        payload = handle_create_payload(entity, content.author)
        # Just dump to the relay system for now
        url = "https://%s/receive/public" % settings.SOCIALHOME_RELAY_DOMAIN
        send_document(url, payload)
    else:
        logger.warning("No entity for %s", content)


def send_content_retraction(content, author_id):
    """Handle sending of retractions.

    Currently only for public content.
    """
    if not content.visibility == Visibility.PUBLIC:
        return
    author = Profile.objects.get(id=author_id)
    entity = make_federable_retraction(content, author)
    if entity:
        if settings.DEBUG:
            # Don't send in development mode
            return
        payload = handle_create_payload(entity, author)
        # Just dump to the relay system for now
        url = "https://%s/receive/public" % settings.SOCIALHOME_RELAY_DOMAIN
        send_document(url, payload)
    else:
        logger.warning("No retraction entity for %s", content)


def forward_relayable(entity, parent_id):
    """Handle forwarding of a relayable object.

    Currently only for public content.
    """
    try:
        parent = Content.objects.get(id=parent_id, visibility=Visibility.PUBLIC)
    except Content.DoesNotExist:
        logger.warning("No public content found with id %s", parent_id)
        return
    if settings.DEBUG:
        # Don't send in development mode
        return
    entity.sign_with_parent(parent.author.private_key)
    payload = handle_create_payload(entity, parent.author)
    # Just dump to the relay system for now
    url = "https://%s/receive/public" % settings.SOCIALHOME_RELAY_DOMAIN
    send_document(url, payload)
