# -*- coding: utf-8 -*-
import pytest
from socialhome.users.tests.factories import UserFactory


@pytest.mark.usefixtures("db", "settings")
class TestProfile(object):
    def test_signal_creates_a_profile(self, settings):
        settings.SOCIALHOME_GENERATE_USER_RSA_KEYS_ON_SAVE = True
        user = UserFactory()
        profile = user.profile
        assert profile.user == user
        assert profile.name == user.name
        assert profile.nickname == user.username
        assert profile.email == user.email
        assert profile.rsa_private_key
        assert profile.rsa_public_key
        assert profile.handle == "%s@%s" %(user.username, settings.SOCIALHOME_DOMAIN)
        assert profile.guid
