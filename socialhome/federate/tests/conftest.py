import pytest

from socialhome.tests.utils import disable_requests


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    """Disable requests calls."""
    disable_requests(monkeypatch)
