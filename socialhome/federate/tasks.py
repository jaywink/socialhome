# -*- coding: utf-8 -*-
import logging

from federation.entities import base
from federation.fetchers import retrieve_remote_profile
from federation.inbound import handle_receive
from federation.entities.diaspora.entities import DiasporaPost
from federation.exceptions import NoSuitableProtocolFoundError

from socialhome.content.models import Post
from socialhome.enums import Visibility
from socialhome.federate.utils import safe_make_aware
from socialhome.taskapp.celery import tasks
from socialhome.users.models import User

logger = logging.getLogger("socialhome")


@tasks.task()
def receive_task(payload, guid=None):
    """Process received payload."""
    # TODO: we're skipping author verification until fetching of remote profile public keys is implemented
    user = None
    if guid:
        try:
            user = User.objects.get(guid=guid, local=True)
        except User.DoesNotExist:
            logger.warning("No local user found with guid")
            return
    try:
        sender, protocol_name, entities = handle_receive(payload, user=user, skip_author_verification=True)
        logger.debug("sender=%s, protocol_name=%s, entities=%s" % (sender, protocol_name, entities))
    except NoSuitableProtocolFoundError:
        logger.warning("No suitable protocol found for payload")
        return
    if not entities:
        logger.warning("No entities in payload")
        return
    sender_user = get_sender_user(sender)
    if not sender_user:
        return
    process_entities(entities, user=sender_user)


def get_sender_user(sender):
    try:
        sender_user = User.objects.get(handle=sender, local=False)
    except User.DoesNotExist:
        remote_profile = retrieve_remote_profile(sender)
        if not remote_profile:
            logger.warning("Remote user not found locally or remotely.")
            return
        sender_user = User.objects.create(
            username=remote_profile.handle.split("@")[0],
            name=remote_profile.name,
            guid=remote_profile.guid,
            handle=remote_profile.handle,
            visibility=Visibility.PUBLIC if remote_profile.public else Visibility.LIMITED,
            rsa_public_key=remote_profile.public_key,
            local=False,
        )
    return sender_user


def process_entities(entities, user):
    """Process a list of entities."""
    for entity in entities:
        logging.info("Entity: %s" % entity)
        if isinstance(entity, base.Post):
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
