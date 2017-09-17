from unittest.mock import Mock

import redis
import requests


class MockRedis(Mock):
    def zrank(self, *args, **kwargs):
        return None

    def zrevrange(self, *args, **kwargs):
        return []


class MockResponse(str):
    status_code = 200
    text = ""

    @staticmethod
    def raise_for_status():
        pass


# Disable certain types of network calls from now on
# This will not be 100% but it should work for those network calls we use
requests.get = Mock(return_value=MockResponse)
requests.post = Mock()
requests.patch = Mock()
requests.delete = Mock()
requests.put = Mock()


# Disable redis connection
redis.StrictRedis = Mock(return_value=MockRedis())
