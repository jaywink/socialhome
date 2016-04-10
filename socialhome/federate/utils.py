# -*- coding: utf-8 -*-
from Crypto import Random
from Crypto.PublicKey import RSA


def generate_rsa_private_key():
    """Generate a new RSA private key."""
    rand = Random.new().read
    return RSA.generate(4096, rand)
