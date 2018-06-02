import datetime

from django.test import RequestFactory

from socialhome.users.tasks.exports import create_user_export
from socialhome.users.templatetags.users import get_user_export_date
from socialhome.users.tests.tasks.test_exports import UserExportTestBase


class TestGetUserExportDate(UserExportTestBase):
    def test_get_export_date(self):
        request = RequestFactory().get("/")
        request.user = self.user
        create_user_export(self.user.id)
        self.assertTrue(isinstance(get_user_export_date({"request": request}), datetime.datetime))
