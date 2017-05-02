import pytest

from socialhome.tests.utils import disable_requests, disable_mailer


@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch):
    """Disable network calls."""
    disable_requests(monkeypatch)
    disable_mailer(monkeypatch)
