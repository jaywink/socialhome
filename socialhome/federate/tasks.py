import logging

from django.conf import settings

from federation.exceptions import NoSuitableProtocolFoundError
from federation.inbound import handle_receive
from federation.outbound import handle_create_payload
from federation.utils.network import send_document

from socialhome.enums import Visibility
from socialhome.federate.utils.tasks import (
    get_sender_profile, process_entities, make_federable_entity, make_federable_retraction
)
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


@tasks.task()
def send_content(content):
    """Handle sending a Content object out via the federation layer.

    Currently we only deliver public content.
    """
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


@tasks.task()
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

