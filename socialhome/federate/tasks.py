import logging

from django.conf import settings
from federation.entities import base
from federation.exceptions import NoSuitableProtocolFoundError, NoSenderKeyFoundError, SignatureVerificationError
from federation.inbound import handle_receive
from federation.outbound import handle_send
from federation.utils.diaspora import generate_diaspora_profile_id

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.enums import Visibility
from socialhome.federate.utils.tasks import (
    process_entities, sender_key_fetcher)
from socialhome.federate.utils import make_federable_profile
from socialhome.federate.utils.entities import make_federable_content, make_federable_retraction
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
    process_entities(entities, receiving_profile=profile)


def send_content(content_id, recipient_id=None):
    """
    Handle sending a Content object out via the federation layer.
    """
    try:
        content = Content.objects.get(
            id=content_id,
            visibility__in=(Visibility.PUBLIC, Visibility.LIMITED),
            content_type=ContentType.CONTENT,
            local=True,
        )
    except Content.DoesNotExist:
        logger.warning("No local content found with id %s", content_id)
        return
    if recipient_id:
        try:
            recipient = Profile.objects.get(id=recipient_id, user__isnull=True)
        except Profile.DoesNotExist:
            logger.warning("No remote recipient found with id %s", recipient_id)
            return
    else:
        recipient = None
    entity = make_federable_content(content)
    if entity:
        if settings.DEBUG:
            # Don't send in development mode
            return
        if recipient:
            recipients = [
                (generate_diaspora_profile_id(recipient.handle, recipient.guid), recipient.key),
            ]
        else:
            recipients = [settings.SOCIALHOME_RELAY_ID]
            recipients.extend(_get_remote_followers(content.author))

        logger.debug("send_content - sending to recipients: %s", recipients)
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
    replies = Content.objects.filter(
        parent_id=target_content.id, visibility=Visibility.PUBLIC, local=False,
    )
    for reply in replies:
        if reply.author.handle != exclude:
            participants.append(generate_diaspora_profile_id(reply.author.handle, reply.author.guid))
    if target_content.content_type == ContentType.CONTENT:
        shares = Content.objects.filter(
            share_of_id=target_content.id, visibility=Visibility.PUBLIC, local=False,
        )
        for share in shares:
            if share.author.handle != exclude:
                participants.append(generate_diaspora_profile_id(share.author.handle, share.author.guid))
            participants = _get_remote_participants_for_content(
                share, participants, exclude=exclude, include_remote=True
            )
    return participants


def _get_remote_followers(profile, exclude=None):
    """Get remote followers for a profile."""
    followers = []
    for follower in Profile.objects.filter(following=profile, user__isnull=True):
        if follower.handle != exclude:
            followers.append(generate_diaspora_profile_id(follower.handle, follower.guid))
    return followers


def _get_limited_recipients(sender, content):
    return [
        (generate_diaspora_profile_id(profile.handle, profile.guid), profile.key)
        for profile in content.limited_visibilities.all() if profile.handle != sender
    ]


def send_reply(content_id):
    """
    Handle sending a Content object that is a reply out via the federation layer.
    """
    try:
        content = Content.objects.get(
            id=content_id,
            visibility__in=(Visibility.PUBLIC, Visibility.LIMITED),
            content_type=ContentType.REPLY,
            local=True,
        )
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
        parent_author = content.parent.author
        if content.visibility == Visibility.PUBLIC:
            recipients = [
                generate_diaspora_profile_id(parent_author.handle, parent_author.guid),
            ]
        else:
            recipients = [
                (generate_diaspora_profile_id(parent_author.handle, parent_author.guid), parent_author.key),
            ]
        logger.debug("send_reply - sending to recipients: %s", recipients)
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
            recipients.append(
                generate_diaspora_profile_id(content.share_of.author.handle, content.share_of.author.guid),
            )
        logger.debug("send_share - sending to recipients: %s", recipients)
        handle_send(entity, content.author, recipients)
    else:
        logger.warning("send_share - No entity for %s", content)


def send_content_retraction(content, author_id):
    """
    Handle sending of retractions for content.
    """
    if content.visibility not in (Visibility.PUBLIC, Visibility.LIMITED) or not content.local:
        return
    author = Profile.objects.get(id=author_id)
    entity = make_federable_retraction(content, author)
    if entity:
        if settings.DEBUG:
            # Don't send in development mode
            return
        if content.visibility == Visibility.PUBLIC:
            recipients = [settings.SOCIALHOME_RELAY_ID]
            recipients.extend(
                _get_remote_followers(author)
            )
        else:
            recipients = _get_limited_recipients(author.handle, content)

        logger.debug("send_content_retraction - sending to recipients: %s", recipients)
        handle_send(entity, author, recipients)
    else:
        logger.warning("send_content_retraction - No retraction entity for %s", content)


def send_profile_retraction(profile):
    """Handle sending of retractions for profiles.

    Only sent for public and limited profiles. Reason: we might actually leak user information
    outside for profiles which were never federated outside if we send for example
    SELF or SITE profile retractions.

    This must be called as a pre_delete signal or it will fail.
    """
    if profile.visibility not in (Visibility.PUBLIC, Visibility.LIMITED) or not profile.is_local:
        return
    entity = make_federable_retraction(profile)
    if entity:
        if settings.DEBUG:
            # Don't send in development mode
            return
        if profile.visibility == Visibility.PUBLIC:
            recipients = [settings.SOCIALHOME_RELAY_ID]
        else:
            recipients = []
        recipients.extend(
            _get_remote_followers(profile)
        )
        logger.debug("send_profile_retraction - sending to recipients: %s", recipients)
        handle_send(entity, profile, recipients)
    else:
        logger.warning("send_profile_retraction - No retraction entity for %s", profile)


def forward_entity(entity, target_content_id):
    """Handle forwarding of an entity related to a target content.

    For example: remote replies on local content, remote shares on local content.
    """
    try:
        target_content = Content.objects.get(
            id=target_content_id,
            visibility__in=(Visibility.PUBLIC, Visibility.LIMITED),
            local=True,
        )
    except Content.DoesNotExist:
        logger.warning("forward_entity - No local content found with id %s", target_content_id)
        return
    try:
        content = Content.objects.get(
            guid=entity.guid, visibility__in=(Visibility.PUBLIC, Visibility.LIMITED),
        )
    except Content.DoesNotExist:
        logger.warning("forward_entity - No content found with guid %s", entity.guid)
        return
    if settings.DEBUG:
        # Don't send in development mode
        return
    if target_content.visibility == Visibility.PUBLIC:
        recipients = _get_remote_participants_for_content(target_content, exclude=entity.handle)
        recipients.extend(_get_remote_followers(
            target_content.author,
            exclude=entity.handle,
        ))
    elif target_content.visibility == Visibility.LIMITED and content.content_type == ContentType.REPLY:
        recipients = _get_limited_recipients(entity.handle, target_content)
    else:
        return
    logger.debug("forward_entity - sending to recipients: %s", recipients)
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
    recipients = [
        (generate_diaspora_profile_id(remote_profile.handle, remote_profile.guid), remote_profile.key),
     ]
    logger.debug("send_follow_change - sending to recipients: %s", recipients)
    handle_send(entity, profile, recipients)
    # Also trigger a profile send
    send_profile(profile_id, recipients=[generate_diaspora_profile_id(remote_profile.handle, remote_profile.guid)])


def send_profile(profile_id, recipients=None):
    """Handle sending a Profile object out via the federation layer.

    :param profile_id: Profile.id of profile to send
    :param recipients: Optional list of recipients, see `federation.outbound.handle_send` parameters
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
    if not recipients:
        recipients = _get_remote_followers(profile)
    logger.debug("send_profile - sending to recipients: %s", recipients)
    handle_send(entity, profile, recipients)
