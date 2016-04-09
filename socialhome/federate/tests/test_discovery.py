# -*- coding: utf-8 -*-
import pytest


@pytest.mark.usefixtures("client")
class TestFederationDiscovery(object):
    def test_host_meta_responds(self, client):
        response = client.get('/.well-known/host-meta')
        assert response.status_code == 200
