from typing import List

from Crypto import Random
from Crypto.PublicKey import RSA
from django.conf import settings

from socialhome.utils import get_redis_connection


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
