import logging
from datetime import datetime
from typing import List

import django_rq
from Crypto import Random
from Crypto.PublicKey import RSA
from django.conf import settings

from federation.utils.network import fetch_document
from socialhome.utils import get_redis_connection

logger = logging.getLogger("socialhome")

workers = django_rq.workers.get_worker_class().all(connection=get_redis_connection())


def generate_rsa_private_key(bits=4096):
    """Generate a new RSA private key."""
    rand = Random.new().read
    return RSA.generate(bits, rand)


def get_pony_urls():
    """Function to return some pony urls which will not change."""
    base_url = "{url}{staticpath}images/pony[size].png".format(
        url=settings.SOCIALHOME_URL, staticpath=settings.STATIC_URL
    )
    return [
        base_url.replace("[size]", "300"), base_url.replace("[size]", "100"), base_url.replace("[size]", "50")
    ]


def get_recently_active_user_ids() -> List[int]:
    """
    Returns a list of ID's for User objects that have been recently active.
    """
    r = get_redis_connection()
    keys = r.keys(r"sh:users:activity:*")
    return [int(key.decode("utf-8").rsplit(":", 1)[1]) for key in keys]


def update_profile_from_fed(profile_id):
    from federation.fetchers import retrieve_remote_profile
    from socialhome.users.models import Profile

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        logger.warning('update_profile - profile id %s not found', profile_id)
        return

    if profile.is_local:
        if not profile.finger:
            Profile.objects.filter(id=profile.id).update(finger=f'{profile.user.username}@{settings.SOCIALHOME_DOMAIN}')
            profile.refresh_from_db()
        return

    if any((
        not profile.finger,
        profile.fid and not (profile.key_id or profile.followers_fid),
        not fetch_document(profile.image_url_small)[0],
        datetime.now(tz=profile.modified.tzinfo) - profile.modified > settings.SOCIALHOME_PROFILE_UPDATE_FREQ)):

        remote_profile = retrieve_remote_profile(profile.fid if profile.fid else profile.handle)
        if remote_profile:
            Profile.from_remote_profile(remote_profile, force=True)
            profile.refresh_from_db()
            logger.info('update_profile - profile %s updated', profile)
        else:
            logger.warning('update_profile - failed to retrieve %s', profile)


def update_profiles(contents):
    """
    Add comment here
    """
    from socialhome.users.models import Profile

    profile_ids = {content.author.id for content in contents}
    for profile_id in profile_ids:
        queue = django_rq.get_queue("lowest")
        job_id = f'update_profile_{profile_id}'
        if job_id in queue.job_ids or job_id in [w.get_current_job_id() for w in workers]:
            logger.warning("update_profile - job found for profile id %s, skipping", profile_id)
        if queue.enqueue(update_profile_from_fed, profile_id, job_id=job_id):
            logger.info("update_profile - queued profile update job for profile id %s", profile_id)
        else:
            logger.warning("update_profile - failed to queue profile update job for profile id %s", profile_id)
