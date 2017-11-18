from unittest.mock import Mock

import requests


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
