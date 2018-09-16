import logging
from typing import List

from django.conf import settings
from django.db.models import Q
from federation.entities import base
from federation.exceptions import NoSuitableProtocolFoundError, NoSenderKeyFoundError, SignatureVerificationError
from federation.inbound import handle_receive
from federation.outbound import handle_send

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.enums import Visibility
from socialhome.federate.utils.tasks import process_entities, sender_key_fetcher
from socialhome.federate.utils import make_federable_profile
from socialhome.federate.utils.entities import make_federable_content, make_federable_retraction
from socialhome.users.models import Profile

logger = logging.getLogger("socialhome")


def receive_task(payload, uuid=None):
    """Process received payload."""
    profile = None
    if uuid:
        try:
            profile = Profile.objects.get(uuid=uuid, user__isnull=False)
        except Profile.DoesNotExist:
            logger.warning("No local profile found with uuid")
            return
    try:
        sender, protocol_name, entities = handle_receive(
            payload, user=profile.federable if profile else None, sender_key_fetcher=sender_key_fetcher,
        )
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
                # TODO fid or handle?
                (recipient.handle, recipient.key, recipient.guid),
            ]
        else:
            recipients = [settings.SOCIALHOME_RELAY_ID]
            recipients.extend(_get_remote_followers(content.author))

        logger.debug("send_content - sending to recipients: %s", recipients)
        handle_send(entity, content.author.federable, recipients)
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
        if reply.author.fid != exclude and reply.author.handle != exclude:
            # TODO fid or handle?
            participants.append(reply.author.handle)
    if target_content.content_type == ContentType.CONTENT:
        shares = Content.objects.filter(
            share_of_id=target_content.id, visibility=Visibility.PUBLIC, local=False,
        )
        for share in shares:
            if share.author.fid != exclude and share.author.handle != exclude:
                # TODO fid or handle?
                participants.append(share.author.handle)
            participants = _get_remote_participants_for_content(
                share, participants, exclude=exclude, include_remote=True
            )
    return participants


def _get_remote_followers(profile, exclude=None):
    """Get remote followers for a profile."""
    followers = []
    for follower in Profile.objects.filter(following=profile, user__isnull=True):
        if follower.fid != exclude and follower.handle != exclude:
            # TODO fid or handle?
            followers.append(follower.handle)
    return followers


def _get_limited_recipients(sender: str, content: Content) -> List:
    return [
        # TODO fid or handle?
        (profile.handle, profile.key, profile.guid)
        for profile in content.limited_visibilities.all()
        if profile.fid != sender and profile.handle != sender and profile.guid != sender
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
                # TODO fid or handle?
                parent_author.handle,
            ]
        else:
            recipients = [
                # TODO fid or handle?
                (parent_author.handle, parent_author.key, parent_author.guid),
            ]
        logger.debug("send_reply - sending to recipients: %s", recipients)
        handle_send(entity, content.author.federable, recipients)


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
                # TODO fid or handle?
                content.share_of.author.handle,
            )
        logger.debug("send_share - sending to recipients: %s", recipients)
        handle_send(entity, content.author.federable, recipients)
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
            recipients = _get_limited_recipients(author.uuid, content)

        logger.debug("send_content_retraction - sending to recipients: %s", recipients)
        handle_send(entity, author.federable, recipients)
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
        handle_send(entity, profile.federable, recipients)
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
        content = Content.objects.fed(entity.id, visibility__in=(Visibility.PUBLIC, Visibility.LIMITED)).get()
    except Content.DoesNotExist:
        logger.warning("forward_entity - No content found with uuid %s", entity.id)
        return
    if settings.DEBUG:
        # Don't send in development mode
        return
    if target_content.visibility == Visibility.PUBLIC:
        recipients = _get_remote_participants_for_content(target_content, exclude=entity.actor_id)
        recipients.extend(_get_remote_followers(
            target_content.author,
            exclude=entity.actor_id,
        ))
    elif target_content.visibility == Visibility.LIMITED and content.content_type == ContentType.REPLY:
        recipients = _get_limited_recipients(entity.actor_id, target_content)
    else:
        return
    logger.debug("forward_entity - sending to recipients: %s", recipients)
    handle_send(entity, content.author.federable, recipients, parent_user=target_content.author.federable)


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
    entity = base.Follow(
        actor_id=profile.fid,
        target_id=remote_profile.fid,
        following=follow,
        handle=profile.handle,
        target_handle=remote_profile.handle,
    )
    recipients = [
        # TODO fid or handle?
        (remote_profile.handle, remote_profile.key, remote_profile.guid),
     ]
    logger.debug("send_follow_change - sending to recipients: %s", recipients)
    handle_send(entity, profile.federable, recipients)
    # Also trigger a profile send
    # TODO fid or handle?
    send_profile(profile_id, recipients=[remote_profile.handle])


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
    handle_send(entity, profile.federable, recipients)
