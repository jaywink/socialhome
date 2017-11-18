import logging

from django.conf import settings
from federation.entities import base
from federation.exceptions import NoSuitableProtocolFoundError, NoSenderKeyFoundError, SignatureVerificationError
from federation.inbound import handle_receive
from federation.outbound import handle_send, handle_create_payload
from federation.utils.network import send_document

from socialhome.content.enums import ContentType
from socialhome.content.models import Content

from socialhome.enums import Visibility
from socialhome.federate.utils.tasks import (
    process_entities, make_federable_content, make_federable_retraction, sender_key_fetcher,
    make_federable_profile)
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
        content = Content.objects.get(id=content_id, visibility=Visibility.PUBLIC, content_type=ContentType.CONTENT,
                                      local=True)
    except Content.DoesNotExist:
        logger.warning("No local content found with id %s", content_id)
        return
    entity = make_federable_content(content)
    if entity:
        if settings.DEBUG:
            # Don't send in development mode
            return
        recipients = [
            (settings.SOCIALHOME_RELAY_DOMAIN, "diaspora"),
        ]
        recipients.extend(_get_remote_followers(content.author))
        handle_send(entity, content.author, recipients)
    else:
        logger.warning("send_content - No entity for %s", content)


def _get_remote_participants_for_content(target_content, participants=None, exclude=None, include_remote=False):
    """Get remote participants for a target content.

    Look at both replies and shares of target local content. Does a recursive call to get also replies of shares,
    even if those shares are remote.
    """
    if not participants:
        participants = []
    if not include_remote and not target_content.local:
        return participants
    replies = Content.objects.filter(parent_id=target_content.id, visibility=Visibility.PUBLIC, local=False)
    for reply in replies:
        if reply.author.handle != exclude:
            participants.append((reply.author.handle, None))
    if target_content.content_type == ContentType.CONTENT:
        shares = Content.objects.filter(share_of_id=target_content.id, visibility=Visibility.PUBLIC, local=False)
        for share in shares:
            if share.author.handle != exclude:
                participants.append((share.author.handle, None))
            participants = _get_remote_participants_for_content(
                share, participants, exclude=exclude, include_remote=True
            )
    return participants


def _get_remote_followers(profile, exclude=None):
    """Get remote followers for a profile."""
    followers = []
    for follower in Profile.objects.filter(following=profile, user__isnull=True):
        if follower.handle != exclude:
            followers.append((follower.handle, None))
    return followers


def send_reply(content_id):
    """Handle sending a Content object that is a reply out via the federation layer.

    Currently we only deliver public content.
    """
    try:
        content = Content.objects.get(id=content_id, visibility=Visibility.PUBLIC, content_type=ContentType.REPLY,
                                      local=True)
    except Content.DoesNotExist:
        logger.warning("No content found with id %s", content_id)
        return
    entity = make_federable_content(content)
    if not entity:
        logger.warning("send_reply - No entity for %s", content)
    if settings.DEBUG:
        # Don't send in development mode
        return
    # Send directly (remote parent) or as a relayable (local parent)
    if content.parent.local:
        forward_entity(entity, content.parent.id)
    else:
        # We only need to send to the original author
        recipients = [
            (content.parent.author.handle, None),
        ]
        handle_send(entity, content.author, recipients)


def send_share(content_id):
    """Handle sending a share of a Content object to the federation layer.

    Currently we only deliver public shares.
    """
    try:
        content = Content.objects.get(id=content_id, visibility=Visibility.PUBLIC, content_type=ContentType.SHARE,
                                      local=True)
    except Content.DoesNotExist:
        logger.warning("No local share found with id %s", content_id)
        return
    entity = make_federable_content(content)
    if entity:
        if settings.DEBUG:
            # Don't send in development mode
            return
        recipients = _get_remote_followers(content.author)
        if not content.share_of.local:
            # Send to original author
            recipients.append((content.share_of.author.handle, None))
        handle_send(entity, content.author, recipients)
    else:
        logger.warning("send_share - No entity for %s", content)


def send_content_retraction(content, author_id):
    """Handle sending of retractions.

    Currently only for public content.
    """
    if not content.visibility == Visibility.PUBLIC or not content.local:
        return
    author = Profile.objects.get(id=author_id)
    entity = make_federable_retraction(content, author)
    if entity:
        if settings.DEBUG:
            # Don't send in development mode
            return
        recipients = [
            (settings.SOCIALHOME_RELAY_DOMAIN, "diaspora"),
        ]
        recipients.extend(_get_remote_followers(author))
        handle_send(entity, author, recipients)
    else:
        logger.warning("send_content_retraction - No retraction entity for %s", content)


def forward_entity(entity, target_content_id):
    """Handle forwarding of an entity related to a target content.

    For example: remote replies on local content, remote shares on local content.

    Currently only for public content.
    """
    try:
        target_content = Content.objects.get(id=target_content_id, visibility=Visibility.PUBLIC, local=True)
    except Content.DoesNotExist:
        logger.warning("forward_entity - No public local content found with id %s", target_content_id)
        return
    try:
        content = Content.objects.get(guid=entity.guid, visibility=Visibility.PUBLIC)
    except Content.DoesNotExist:
        logger.warning("forward_entity - No content found with guid %s", entity.guid)
        return
    if settings.DEBUG:
        # Don't send in development mode
        return
    recipients = _get_remote_participants_for_content(target_content, exclude=entity.handle)
    recipients.extend(_get_remote_followers(target_content.author, exclude=entity.handle))
    handle_send(entity, content.author, recipients, parent_user=target_content.author)


def send_follow_change(profile_id, followed_id, follow):
    """Handle sending of a local follow of a remote profile."""
    try:
        profile = Profile.objects.get(id=profile_id, user__isnull=False)
    except Profile.DoesNotExist:
        logger.warning("send_follow_change - No local profile %s found to send follow with", profile_id)
        return
    try:
        remote_profile = Profile.objects.get(id=followed_id, user__isnull=True)
    except Profile.DoesNotExist:
        logger.warning("send_follow_change - No remote profile %s found to send follow for", followed_id)
        return
    if settings.DEBUG:
        # Don't send in development mode
        return
    entity = base.Follow(handle=profile.handle, target_handle=remote_profile.handle, following=follow)
    # TODO: add high level method support to federation for private payload delivery
    payload = handle_create_payload(entity, profile, to_user=remote_profile)
    url = "https://%s/receive/users/%s" % (
        remote_profile.handle.split("@")[1], remote_profile.guid,
    )
    send_document(url, payload)
    # Also trigger a profile send
    send_profile(profile_id, recipients=[(remote_profile.handle, None)])


def send_profile(profile_id, recipients=None):
    """Handle sending a Profile object out via the federation layer.

    :param profile_id: Profile.id of profile to send
    :param recipients: Optional list of recipient tuples, in form tuple(handle, network), for example
        ("foo@example.com", "diaspora"). Network can be None.
    """
    try:
        profile = Profile.objects.get(id=profile_id, user__isnull=False)
    except Profile.DoesNotExist:
        logger.warning("send_profile - No local profile found with id %s", profile_id)
        return
    entity = make_federable_profile(profile)
    if not entity:
        logger.warning("send_profile - No entity for %s", profile)
        return
    if settings.DEBUG:
        # Don't send in development mode
        return
    # From diaspora devs: "if the profile is private it needs to be encrypted, so to the private endpoint,
    # starting with 0.7.0.0 diaspora starts sending public profiles to the public endpoint only once per pod".
    # Let's just send everything to private endpoints as 0.7 isn't out yet.
    # TODO: once 0.7 is out for longer, start sending public profiles to public endpoints
    # TODO: add high level method support to federation for private payload delivery
    if not recipients:
        recipients = _get_remote_followers(profile)
    for handle, _network in recipients:
        try:
            remote_profile = Profile.objects.get(handle=handle)
        except Profile.DoesNotExist:
            continue
        payload = handle_create_payload(entity, profile, to_user=remote_profile)
        url = "https://%s/receive/users/%s" % (handle.split("@")[1], remote_profile.guid)
        send_document(url, payload)
