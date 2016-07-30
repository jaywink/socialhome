# -*- coding: utf-8 -*-
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
