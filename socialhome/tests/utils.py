import tempfile
from unittest.mock import Mock

from PIL import Image
from django.contrib.sites.shortcuts import get_current_site
from django.test import override_settings, TransactionTestCase, RequestFactory
from rest_framework.test import APITestCase
from test_plus import TestCase
from test_plus.test import CBVTestCase

import socialhome.tests.environment  # Set some environment tweaks
from socialhome.content.tests.factories import (
    PublicContentFactory, SiteContentFactory, SelfContentFactory, LimitedContentFactory)
from socialhome.users.tests.factories import PublicProfileFactory, PublicUserFactory


class CreateDataMixin:
    user = None
    profile = None
    remote_profile = None
    public_content = None
    site_content = None
    self_content = None
    limited_content = None

    @staticmethod
    def create_local_and_remote_user(target):
        target.user = PublicUserFactory()
        target.profile = target.user.profile
        target.remote_profile = PublicProfileFactory()

    @staticmethod
    def create_content_set(target, author=None):
        if not author:
            author = PublicProfileFactory()
        target.public_content = PublicContentFactory(author=author)
        target.site_content = SiteContentFactory(author=author)
        target.self_content = SelfContentFactory(author=author)
        target.limited_content = LimitedContentFactory(author=author)


class SocialhomeTestBase(CreateDataMixin):
    maxDiff = None

    @classmethod
    def create_local_and_remote_user(cls):
        CreateDataMixin.create_local_and_remote_user(cls)

    @classmethod
    def create_content_set(cls, author=None):
        CreateDataMixin.create_content_set(cls, author=author)

    @staticmethod
    def get_request(user, path="/"):
        request = RequestFactory().get(path)
        request.user = user
        request.site = get_current_site(request)
        return request

    @staticmethod
    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def get_temp_image():
        image = Image.new("RGB", (100, 100))
        tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
        image.save(tmp_file)
        tmp_file.seek(0)
        return tmp_file


class SocialhomeTestCase(SocialhomeTestBase, TestCase):
    pass


class SocialhomeCBVTestCase(SocialhomeTestBase, CBVTestCase):
    pass


class SocialhomeAPITestCase(SocialhomeTestBase, APITestCase, TestCase):
    pass


class SocialhomeTransactionTestCase(CreateDataMixin, TransactionTestCase):
    maxDiff = None

    def create_local_and_remote_user(self):
        CreateDataMixin.create_local_and_remote_user(self)

    def create_content_set(self, author=None):
        CreateDataMixin.create_content_set(self, author=author)


# py.test monkeypatches while we still have two kinds of tests
# Remove these once all our tests are either `SocialhomeTestCase` or another test class
def disable_requests(monkeypatch):
    """Mock away request.get and requests.post."""
    monkeypatch.setattr("requests.post", Mock())

    class MockResponse(str):
        status_code = 200
        text = ""

        @staticmethod
        def raise_for_status():
            pass

    monkeypatch.setattr("requests.get", Mock(return_value=MockResponse))


def disable_mailer(monkeypatch):
    """Mock away mail sending."""
    monkeypatch.setattr("django.core.mail.send_mail", Mock())
