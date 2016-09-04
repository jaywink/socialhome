import logging

import requests
from django.conf import settings

from federation.exceptions import NoSuitableProtocolFoundError
from federation.inbound import handle_receive
from federation.outbound import handle_create_payload

from socialhome.enums import Visibility
from socialhome.federate.utils.tasks import get_sender_profile, process_entities, make_federable_entity
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

    TODO: parts of this should really be in Social-Federation. We should be able to just
    convert our Content to Social-Federation entities and call a simple send method that just works.
    """
    if not content.visibility == Visibility.PUBLIC:
        return
    # TODO: Social-Federation requires changing to not require a `to_user` on public content
    # Use a mock contact object for now
    class MockContact(object):
        key = None
    entity = make_federable_entity(content)
    if entity:
        payload = handle_create_payload(content.author, MockContact(), entity)
        # Just dump to the relay system for now
        # TODO: implement send_document helper in Social-Federation
        url = "https://%s/receive/public" % settings.SOCIALHOME_RELAY_DOMAIN
        logger.debug("Sending document to %s: %s", url, payload)
        try:
            response = requests.post(url, payload, headers={'user-agent': "socialhome/0.1"})
            logger.debug("Response: %s", response)
        except Exception as ex:
            logger.exception("Error sending entity %s: %s", entity, ex)
    else:
        logger.info("No entity for %s", content)
