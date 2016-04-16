# -*- coding: utf-8 -*-
import logging

from federation.controllers import handle_receive
from federation.entities.diaspora.entities import DiasporaPost
from federation.exceptions import NoSuitableProtocolFoundError

from socialhome.content.models import Post
from socialhome.federate.utils import safe_make_aware
from socialhome.taskapp.celery import tasks
from socialhome.users.models import User

logger = logging.getLogger("socialhome")


@tasks.task()
def receive_public_task(payload):
    """Process payload from /receive/public queue."""
    # TODO: we're skipping author verification until fetching of remote profile public keys is implemented
    try:
        sender, protocol_name, entities = handle_receive(payload, skip_author_verification=True)
        logger.debug("sender=%s, protocol_name=%s, entities=%s" % (sender, protocol_name, entities))
    except NoSuitableProtocolFoundError:
        logger.warning("No suitable protocol found for payload")
        return
    if protocol_name != "diaspora":
        logger.warning("Unsupported protocol: %s, sender: %s" % (protocol_name, sender))
        return
    if not entities:
        logger.warning("No entities in payload")
        return
    process_entities(entities)


def process_entities(entities):
    """Process a list of entities."""
    user = None
    for entity in entities:
        logging.info("Entity: %s" % entity)
        # We only care about Diaspora posts atm
        if isinstance(entity, DiasporaPost):
            if not user:
                # TODO: Don't use a dummy user once we have remote profiles
                user, created = User.objects.get_or_create(username="dummy")
            try:
                values = {
                    "text": entity.raw_content, "user": user, "public": entity.public,
                    "remote_created": safe_make_aware(entity.created_at, "UTC"),
                    "service_label": entity.provider_display_name or "",
                }
                post, created = Post.objects.update_or_create(guid=entity.guid, defaults=values)
                if created:
                    logger.info("Saved Post: %s" % post)
                else:
                    logger.info("Updated Post: %s" % post)
            except Exception:
                logger.exception("Failed to handle %s: %s" % (entity.guid, entity.__name__))
