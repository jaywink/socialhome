import logging
from datetime import datetime
from typing import List

from Crypto import Random
from Crypto.PublicKey import RSA
from django.conf import settings

from federation.protocols.enums import ProtocolType

from socialhome.users.tasks import federation
from socialhome.utils import get_redis_connection

logger = logging.getLogger("socialhome")


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


def update_profile(profile, force=False):
    """
    Decide if a profile update should be scheduled if any of the following criteria
    is true:
    - force is True
    - unset listed properties (for local profiles, set and return immediately)
    - unset key_id or followers_fid property for AP profiles
    - more than SOCIALHOME_PROFILE_UPDATE_FREQ days since the last update
    """
    from socialhome.users.models import Profile

    if profile.is_local:
        kwargs = {}
        if not profile.finger: kwargs['finger'] = f'{profile.user.username}@{settings.SOCIALHOME_DOMAIN}'
        if not profile.protocols: kwargs['protocols'] = (ProtocolType.ACTIVITYPUB, ProtocolType.DIASPORA)

        if kwargs: Profile.objects.filter(id=profile.id).update(**kwargs)
        return

    if any((
        force,
        not profile.avatar_url,
        not profile.finger,
        not profile.remote_url,
        not profile.protocols,
        profile.fid and not (profile.key_id or profile.followers_fid),
        datetime.now(tz=profile.modified.tzinfo) - profile.modified > settings.SOCIALHOME_PROFILE_UPDATE_FREQ),
    ):
        federation.update_profile_from_fed.send(profile.id, queue_once_id=str(profile.id))
        logger.info("update_profile - queued profile update job for profile %s", profile)


def update_profiles(contents):
    """
    This function builds a set of unique profiles extracted from
    the provided contents list.
    """
    profiles = {content.author for content in contents}
    for profile in profiles:
        update_profile(profile)
