import django_rq
import logging
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save, m2m_changed, post_delete, pre_delete
from django.dispatch import receiver
from federation.entities.activitypub.enums import ActivityType

from socialhome.federate.tasks import send_follow_change, send_profile, send_profile_retraction
from socialhome.notifications.tasks import send_follow_notification, send_account_approval_admin_notification
from socialhome.streams.streams import update_profile_for_streams
from socialhome.users.models import User, Profile

logger = logging.getLogger("socialhome")


@receiver(post_save, sender=User)
def user_post_save(sender, **kwargs):
    user = kwargs.get("instance")
    if kwargs.get("created"):
        # Create the user profile
        profile = Profile.objects.create(
            user=user,
            name=user.name,
            email=user.email,
            handle="%s@%s" % (user.username, settings.SOCIALHOME_DOMAIN),
            finger="%s@%s" % (user.username, settings.SOCIALHOME_DOMAIN),
        )
        if settings.SOCIALHOME_GENERATE_USER_RSA_KEYS_ON_SAVE:
            profile.generate_new_rsa_key()

        # If users require approval, email the admin
        if settings.ACCOUNT_SIGNUP_REQUIRE_ADMIN_APPROVAL:
            django_rq.enqueue(send_account_approval_admin_notification, user_id=user.id)
    # Initialize and copy pictures to profile
    user.init_pictures_on_disk()
    user.copy_picture_to_profile()


def on_commit_profile_following_change(action, pks, instance):
    for _id in pks:
        if instance.user:
            # Create an activity
            # UNDO is a bit silly, but that is the activity that is done in AP
            # Maybe we should use local activity verbs instead of the federation library?
            activity_type = ActivityType.FOLLOW if action == "post_add" else ActivityType.UNDO
            instance.create_activity(activity_type, object_id=_id)
        # Send out on the federation layer if local follower, remote followed/unfollowed
        if Profile.objects.filter(id=_id, user__isnull=True).exists() and instance.user:
            queue = django_rq.get_queue("high")
            queue.enqueue(
                send_follow_change, instance.id, _id, True if action == "post_add" else False
            )
        # Send out notification if local followed
        if action == "post_add" and Profile.objects.filter(id=_id, user__isnull=False):
            queue = django_rq.get_queue("low")
            queue.enqueue(send_follow_notification, instance.id, _id)


@receiver(m2m_changed, sender=Profile.following.through)
def profile_following_change(sender, instance, action, pk_set, **kwargs):
    """Deliver notification on new followers."""
    if action in ["post_add", "post_remove"]:
        transaction.on_commit(lambda: on_commit_profile_following_change(action, pk_set, instance))


@receiver(post_save, sender=Profile)
def profile_post_save(instance, **kwargs):
    if instance.is_local:
        transaction.on_commit(lambda: federate_profile(instance))
    update_profile_for_streams(instance)


def federate_profile(profile):
    """Send out local profiles to the federation layer."""
    try:
        queue = django_rq.get_queue("high")
        transaction.on_commit(lambda: queue.enqueue(send_profile, profile.id))
    except Exception as ex:
        logger.exception("Failed to federate profile %s: %s", profile, ex)


@receiver(pre_delete, sender=Profile)
def federate_profile_retraction(instance, **kwargs):
    """Send out local profile retractions to the federation layer."""
    if instance.is_local:
        logger.debug('federate_profile_retraction: Got local profile %s delete, sending out retraction', instance)
        try:
            # Don't enqueue, we must complete this before doing the delete
            send_profile_retraction(instance)
        except Exception as ex:
            logger.exception("Failed to federate_profile_retraction %s: %s", instance, ex)


@receiver(post_delete, sender=User, dispatch_uid='delete_user_pictures')
def delete_user_pictures(sender, instance, **kwargs):
    """
    Deletes all user picture copies from disk.
    """
    if instance.picture:
        try:
            logger.debug('delete_user_pictures: Deleting user pictures for %s', instance)
            # Deletes Image Renditions
            instance.picture.delete_all_created_images()
            # Deletes Original Image
            instance.picture.delete(save=False)
        except Exception:
            logger.exception('delet_user_pictures: Failed to delete %s user pictures from disk', instance)
