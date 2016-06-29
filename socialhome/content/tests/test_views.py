import pytest


@pytest.mark.usefixtures("admin_client")
@pytest.mark.usefixtures("settings")
class TestRootProfile(object):
    def test_home_view_rendered_without_root_profile(self, admin_client, settings):
        settings.SOCIALHOME_ROOT_PROFILE = None
        response = admin_client.get("/")
        assert response.templates[0].name == "pages/home.html"

    def test_home_view_rendered_with_root_profile(self, admin_client, settings):
        settings.SOCIALHOME_ROOT_PROFILE = "admin"
        response = admin_client.get("/")
        assert response.templates[0].name == "users/user_detail.html"
