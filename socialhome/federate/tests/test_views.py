# -*- coding: utf-8 -*-
from unittest.mock import patch

import pytest
from django.core.urlresolvers import reverse

from socialhome.users.models import Profile
from socialhome.users.tests.factories import UserFactory


@pytest.mark.usefixtures("db", "client")
class TestFederationDiscovery(object):
    def test_host_meta_responds(self, client):
        response = client.get(reverse("federate:host-meta"))
        assert response.status_code == 200

    def test_webfinger_responds_404_on_unknown_user(self, client):
        response = client.get("{url}?q=foobar%40socialhome.local".format(url=reverse("federate:webfinger")))
        assert response.status_code == 404

    def test_webfinger_responds_200_on_known_user(self, client):
        UserFactory(username="foobar")
        Profile.objects.filter(user__username="foobar").update(rsa_public_key="fooobar")
        response = client.get("{url}?q=foobar%40socialhome.local".format(url=reverse("federate:webfinger")))
        assert response.status_code == 200
        response = client.get("{url}?q=acct%3Afoobar%40socialhome.local".format(url=reverse("federate:webfinger")))
        assert response.status_code == 200

    def test_hcard_responds_on_404_on_unknown_user(self, client):
        response = client.get(reverse("federate:hcard", kwargs={"guid": "fehwuyfehiufhewiuhfiuhuiewfew"}))
        assert response.status_code == 404
        with patch("socialhome.federate.views.get_object_or_404") as mock_get:
            # Test also ValueError raising ending up as 404
            Profile.objects.filter(user__username="foobar").update(rsa_public_key="fooobar")
            mock_get.side_effect = ValueError()
            response = client.get(reverse("federate:hcard", kwargs={"guid": "foobar"}))
            assert response.status_code == 404

    def test_hcard_responds_on_200_on_known_user(self, client):
        user = UserFactory(username="foobar")
        Profile.objects.filter(user__username="foobar").update(rsa_public_key="fooobar")
        response = client.get(reverse("federate:hcard", kwargs={"guid": user.profile.guid}))
        assert response.status_code == 200

    def test_nodeinfo_wellknown_responds(self, client):
        response = client.get(reverse("federate:nodeinfo-wellknown"))
        assert response.status_code == 200

    def test_nodeinfo_responds(self, client):
        response = client.get(reverse("federate:nodeinfo"))
        assert response.status_code == 200

    def test_social_relay_responds(self, client):
        response = client.get(reverse("federate:social-relay"))
        assert response.status_code == 200


@pytest.mark.usefixtures("db", "client")
class TestReceivePublic(object):
    def test_receive_public_responds(self, client):
        response = client.post(reverse("federate:receive-public"), {"xml": "foo"})
        assert response.status_code == 202

    def test_receive_public_returns_bad_request_if_no_payload(self, client):
        response = client.post(reverse("federate:receive-public"))
        assert response.status_code == 400


@pytest.mark.usefixtures("db", "client")
class TestReceiveUser(object):
    def test_receive_user_responds(self, client):
        response = client.post(reverse("federate:receive-user", kwargs={"guid": "1234"}), {"xml": "foo"})
        assert response.status_code == 202

    def test_receive_user_returns_bad_request_if_no_payload(self, client):
        response = client.post(reverse("federate:receive-user", kwargs={"guid": "1234"}))
        assert response.status_code == 400
