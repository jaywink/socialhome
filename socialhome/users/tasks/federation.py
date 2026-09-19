from asgiref.sync import sync_to_async
import dramatiq
import logging
from django.conf import settings

logger = logging.getLogger("socialhome")


@dramatiq.actor(priority=settings.DRAMATIQ_PRIORITY_LOW)
async def update_profile_from_fed(profile_id, **kwargs):
    from federation.fetchers import retrieve_remote_profile
    from socialhome.users.models import Profile

    try:
        profile = await Profile.objects.aget(id=profile_id)
    except Profile.DoesNotExist:
        logger.warning('update_profile - profile id %s not found', profile_id)
        return

    remote_profile = await retrieve_remote_profile(profile.fid if profile.fid else profile.handle)
    if remote_profile:
        await sync_to_async(Profile.from_remote_profile)(remote_profile, force=True)
        await profile.arefresh_from_db()
        logger.info('update_profile - profile %s updated', profile)
    else:
        logger.warning('update_profile - failed to retrieve %s', profile)
