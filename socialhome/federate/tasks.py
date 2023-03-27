from datetime import datetime, timezone, timedelta
import logging
from typing import List, TYPE_CHECKING, Optional
from uuid import uuid4

import django_rq
from django.conf import settings
from dynamic_preferences.registries import global_preferences_registry
from federation.entities import base
from federation.entities.activitypub.constants import NAMESPACE_PUBLIC
from federation.entities.activitypub.enums import ActivityType
from federation.exceptions import NoSuitableProtocolFoundError, NoSenderKeyFoundError, SignatureVerificationError
from federation.inbound import handle_receive
from federation.outbound import handle_send

from socialhome.activities.models import Activity
from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.enums import Visibility
from socialhome.federate.models import Payload
from socialhome.federate.utils.tasks import process_entities, sender_key_fetcher, process_replies
from socialhome.federate.utils import make_federable_profile, get_outbound_payload_logger
from socialhome.federate.utils.entities import make_federable_content, make_federable_retraction
from socialhome.users.models import Profile

if TYPE_CHECKING:
    from federation import RequestType

logger = logging.getLogger("socialhome")


def receive_task(request, uuid=None):
    # type: (RequestType, Optional[str]) -> None
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
            request, user=profile.federable if profile else None, sender_key_fetcher=sender_key_fetcher,
        )
        logger.debug("sender=%s, protocol_name=%s, entities=%s" % (sender, protocol_name, entities))
        preferences = global_preferences_registry.manager()
        if preferences["admin__log_all_receive_payloads"]:
            Payload.objects.create(
                body=request.body,
                direction="inbound",
                entities_found=len(entities),
                headers=request.headers,
                method=request.method,
                protocol=protocol_name or "",
                sender=sender or "",
                url=request.url,
            )
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


def send_content(content_id, activity_fid, recipient_id=None):
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
        entity.activity_id = activity_fid
        if settings.DEBUG and settings.SOCIALHOME_DOMAIN.startswith('127.0'):
            # Don't send in development mode
            return
        recipients = []
        if recipient:
            recipients.append(recipient.get_recipient_for_visibility(content.visibility))
        else:
            if content.visibility == Visibility.PUBLIC:
                # If we have Matrix support enabled, also add the appservice
                if settings.SOCIALHOME_MATRIX_ENABLED:
                    recipients.append(content.author.get_recipient_for_matrix_appservice())
            recipients.extend(_get_remote_followers(content.author, content.visibility))

        logger.debug("send_content - sending to recipients: %s", recipients)
        handle_send(entity, content.author.federable, recipients, payload_logger=get_outbound_payload_logger())
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
    replies = Content.objects.filter(root_parent_id=target_content.id, local=False, author__user__isnull=True)
    for reply in replies:
        if not exclude or (reply.author.fid != exclude and reply.author.handle != exclude):
            participants.append(reply.author.get_recipient_for_visibility(target_content.visibility))
    if target_content.content_type == ContentType.CONTENT:
        shares = Content.objects.filter(share_of_id=target_content.id, local=False)
        for share in shares:
            if not exclude or (share.author.fid != exclude and share.author.handle != exclude):
                participants.append(share.author.get_recipient_for_visibility(target_content.visibility))
            participants = _get_remote_participants_for_content(
                share, participants, exclude=exclude, include_remote=True
            )
    return participants


def _get_remote_followers(profile: Profile, visibility: Visibility, exclude=None):
    """Get remote followers for a profile."""
    followers = []
    for follower in Profile.objects.filter(following=profile, user__isnull=True):
        if not exclude or (follower.fid != exclude and follower.handle != exclude):
            followers.append(follower.get_recipient_for_visibility(visibility))
    return followers


def _get_limited_recipients(sender: str, content: Content) -> List:
    profiles = []
    for profile in content.limited_visibilities.all():
        if profile.fid != sender and profile.handle != sender and profile.guid != sender:
            profiles.append(profile.get_recipient_for_visibility(content.visibility))
    return profiles


def send_reply(content_id, activity_fid):
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
    entity.activity_id = activity_fid
    if settings.DEBUG and settings.SOCIALHOME_DOMAIN.startswith('127.0'):
        # Don't send in development mode
        return
    recipients = []
    if not content.root_parent.author.is_local:
        recipients.append(content.root_parent.author.get_recipient_for_visibility(content.visibility))
    if content.visibility == Visibility.PUBLIC:
        recipients.extend(
            _get_remote_participants_for_content(content, exclude=content.author.fid, include_remote=True),
        )
        recipients.extend(_get_remote_followers(
            content.author,
            content.visibility,
            exclude=content.author.fid,
        ))
    elif content.visibility == Visibility.LIMITED:
        recipients.extend(_get_limited_recipients(content.author.fid, content))
    else:
        return
    if not recipients:
        logger.debug("send_reply - no remote recipients for content: %s", content.id)
        return
    logger.debug("send_reply - sending to recipients: %s", recipients)
    handle_send(entity, content.author.federable, recipients, payload_logger=get_outbound_payload_logger())


def send_share(content_id, activity_fid):
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
        entity.id = activity_fid
        if settings.DEBUG and settings.SOCIALHOME_DOMAIN.startswith('127.0'):
            # Don't send in development mode
            return
        recipients = _get_remote_followers(content.author, content.visibility)
        if not content.share_of.local:
            # Send to original author
            recipients.append(content.share_of.author.get_recipient_for_visibility(content.visibility))
        logger.debug("send_share - sending to recipients: %s", recipients)
        handle_send(entity, content.author.federable, recipients, payload_logger=get_outbound_payload_logger())
        target_content = content.share_of
        if target_content.replies_fid:
            queue = django_rq.get_queue('low')
            content_id = target_content.id if target_content.content_type == ContentType.CONTENT else target_content.root_parent_id
            if django_rq.get_scheduler(queue=queue).enqueue_in(timedelta(seconds=90),
                    process_replies, content_id, shared_by_id=content.id):
                logger.info("send_share - queued process_replies job for content id %s", content_id)
            else:
                logger.warn("send_share - failed to enqueue process_replies job for content id %s", content_id)
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
        if settings.DEBUG and settings.SOCIALHOME_DOMAIN.startswith('127.0'):
            # Don't send in development mode
            return
        if content.visibility == Visibility.PUBLIC:
            recipients = _get_remote_followers(author, content.visibility)
        else:
            recipients = _get_limited_recipients(author.fid, content)

        logger.debug("send_content_retraction - sending to recipients: %s", recipients)
        # Queue to the background since sending could take a while
        queue = django_rq.get_queue("high")
        queue.enqueue(
            handle_send, entity, author.federable, recipients, payload_logger=get_outbound_payload_logger(),
            job_timeout=10000,
        )
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
        if settings.DEBUG and settings.SOCIALHOME_DOMAIN.startswith('127.0'):
            # Don't send in development mode
            return
        recipients = _get_remote_followers(profile, profile.visibility)
        logger.debug("send_profile_retraction - sending to recipients: %s", recipients)
        handle_send(entity, profile.federable, recipients, payload_logger=get_outbound_payload_logger())
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
    if settings.DEBUG and settings.SOCIALHOME_DOMAIN.startswith('127.0'):
        # Don't send in development mode
        return
    if target_content.visibility == Visibility.PUBLIC:
        recipients = _get_remote_participants_for_content(target_content, exclude=entity.actor_id)
        recipients.extend(_get_remote_followers(
            target_content.author,
            target_content.visibility,
            exclude=entity.actor_id,
        ))
    elif target_content.visibility == Visibility.LIMITED and content.content_type == ContentType.REPLY:
        recipients = _get_limited_recipients(entity.actor_id, target_content)
    else:
        return
    logger.debug("forward_entity - sending to recipients: %s", recipients)
    handle_send(
        entity, content.author.federable, recipients, parent_user=target_content.author.federable,
        payload_logger=get_outbound_payload_logger(),
    )


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
    if settings.DEBUG and settings.SOCIALHOME_DOMAIN.startswith('127.0'):
        # Don't send in development mode
        return
    activity = Activity.objects.filter(profile=profile, object_id=remote_profile.id, type=ActivityType.FOLLOW).last()
    entity = base.Follow(
        activity_id=getattr(activity, 'fid', f'{profile.fid}#follow-{uuid4()}'),
        actor_id=profile.fid,
        target_id=remote_profile.fid,
        following=follow,
        handle=profile.handle,
        target_handle=remote_profile.handle,
    )
    # Explicitly use limited visibility to force private endpoint
    recipients = [remote_profile.get_recipient_for_visibility(Visibility.LIMITED)]
    logger.debug("send_follow_change - sending to recipients: %s", recipients)
    handle_send(entity, profile.federable, recipients, payload_logger=get_outbound_payload_logger())
    # Also trigger a profile send
    if follow: send_profile(profile_id, recipients=recipients)


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
    if hasattr(entity, 'times'):
        entity.times['edited'] = (datetime.now(timezone.utc)-profile.modified)< timedelta(seconds=60)
    if settings.DEBUG and settings.SOCIALHOME_DOMAIN.startswith('127.0'):
        # Don't send in development mode
        return
    if not recipients:
        # If we have Matrix support enabled, also add the appservice
        if settings.SOCIALHOME_MATRIX_ENABLED:
            recipients = [profile.get_recipient_for_matrix_appservice()]
        else:
            recipients = []
        recipients.extend(_get_remote_followers(profile, profile.visibility))
        to = NAMESPACE_PUBLIC
    else:
        to = [recipient['fid'] for recipient in recipients if recipient.get('fid', None)]
    if hasattr(entity, 'to'): entity.to = to

    logger.debug("send_profile - sending to recipients: %s", recipients)
    handle_send(entity, profile.federable, recipients, payload_logger=get_outbound_payload_logger())
