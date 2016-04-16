# -*- coding: utf-8 -*-
import pytest
from django.core.urlresolvers import reverse


@pytest.mark.usefixtures("db", "client")
class TestFederationPayloads(object):
    def test_receive_public_responds(self, client):
        response = client.post(reverse("federate:receive-public"), {"xml": "foo"})
        assert response.status_code == 202
