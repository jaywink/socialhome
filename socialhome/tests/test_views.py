import pytest


@pytest.mark.usefixtures("db")
class TestBaseView(object):
    @pytest.mark.usefixtures("client", "settings")
    def test_signup_link_do_not_show_when_signup_are_closed(self, client, settings):
        settings.ACCOUNT_ALLOW_REGISTRATION = False
        response = client.get("/")
        assert "/accounts/signup/" not in str(response.content)

    @pytest.mark.usefixtures("client", "settings")
    def test_signup_link_shows_when_signup_are_opened(self, client, settings):
        settings.ACCOUNT_ALLOW_REGISTRATION = True
        response = client.get("/")
        assert "/accounts/signup/" in str(response.content)
