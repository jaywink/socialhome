from Crypto import Random
from Crypto.PublicKey import RSA
from django.conf import settings


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
