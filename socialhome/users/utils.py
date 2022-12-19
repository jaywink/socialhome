import logging
from typing import List
from urllib.parse import urlparse

from Crypto import Random
from Crypto.PublicKey import RSA
from django.conf import settings

from federation.utils.activitypub import get_profile_id_from_webfinger
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


def set_profile_finger(profile):
    """ 
    To avoid going through all profiles in one shot
    (which could take quite a while due the the webfinger
    query) we call this from profile serializers. It should
    eventually become a noop
    """
    from socialhome.users.models import Profile
    profile.refresh_from_db()
    if not profile.finger: 
        finger = ""
        if profile.is_local or profile.protocol == 'diaspora':
            finger = profile.handle
        elif profile.protocol == 'activitypub':
            domain = urlparse(profile.fid).netloc
            user = profile.fid.strip('/').split('/')[-1]
            webf = f'{user}@{domain}'
            if get_profile_id_from_webfinger(webf) == profile.fid:
                finger = webf
        if finger:
            Profile.objects.filter(id=profile.id).update(finger=finger)
            logger.info(f"finger set to {finger} for {profile}")
        else:
            # should we raise an error here? should the profile be removed?
            logger.error(f"failed to set finger to {finger} for {profile}: could not be retrieved")
