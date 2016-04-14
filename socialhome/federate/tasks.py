# -*- coding: utf-8 -*-
import logging

from federation.controllers import handle_receive
from federation.entities.diaspora.entities import DiasporaPost
from federation.exceptions import NoSuitableProtocolFoundError

from socialhome.content.models import Post
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
    user = None
    for entity in entities:
        logging.info("Entity: %s" % entity)
        # We only care about Diaspora posts atm
        if isinstance(entity, DiasporaPost):
            if not user:
                # TODO: Don't use a dummy user once we have remote profiles
                user = User.objects.get_or_create(username="dummy")
            try:
                post = Post.objects.create(
                    text=entity.raw_content,
                    guid=entity.guid,
                    user=user,
                    public=entity.public,
                    remote_created=entity.created_at,
                    service_label=entity.provider_display_name,
                )
                logger.info("Saved Post: %s" % post)
            except Exception:
                logger.exception("Failed to save Post: %s" % entity.guid)

