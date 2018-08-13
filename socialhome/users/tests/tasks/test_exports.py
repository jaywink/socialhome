import os
from unittest.mock import patch

from django.conf import settings
from django.test import override_settings
from freezegun import freeze_time

from socialhome.content.enums import ContentType
from socialhome.content.tests.factories import ContentFactory
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tasks.exports import UserExporter, create_user_export
from socialhome.users.tests.factories import UserFactory, PublicProfileFactory


@freeze_time('2018-05-30')
@override_settings(SOCIALHOME_EXPORTS_PATH='/tmp/socialhome/exports')
class UserExportTestBase(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def setUp(self):
        super().setUp()
        export_path = '%s/%s' % (settings.SOCIALHOME_EXPORTS_PATH, self.user.id)
        if os.path.isdir(export_path):
            for file in os.listdir(export_path):
                os.unlink(os.path.join(export_path, file))


class TestCreateUserExport(UserExportTestBase):
    def test_export_create(self):
        create_user_export(self.user.id)
        self.assertTrue(
            os.path.isfile(
                os.path.join(settings.SOCIALHOME_EXPORTS_PATH, '%s' % self.user.id, '127.0.0.1:8000-2018-05-30.zip')
            )
        )


class TestUserExporter(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = cls.user.profile
        cls.follower = PublicProfileFactory()
        cls.follower2 = PublicProfileFactory()
        cls.profile.following.add(cls.follower)
        cls.profile.following.add(cls.follower2)
        cls.content = ContentFactory(author=cls.profile)
        cls.content2 = ContentFactory(author=cls.follower)
        cls.reply = ContentFactory(author=cls.profile, parent=cls.content2, content_type=ContentType.REPLY)
        cls.share = ContentFactory(author=cls.profile, share_of=cls.content2, content_type=ContentType.SHARE)

    def setUp(self):
        self.exporter = UserExporter(user=self.user)

    def test_collect_data(self):
        self.exporter.create()
        self.assertTrue("user" in self.exporter.data)
        self.assertTrue("profile" in self.exporter.data)
        self.assertEqual(len(self.exporter.data.get('following')), 2)
        contents = self.exporter.data.get('content')
        self.assertEqual(len(contents), 3)
        self.assertEqual(contents[0].get('uuid'), self.content.uuid)
        self.assertEqual(contents[1].get('uuid'), self.reply.uuid)
        self.assertEqual(contents[2].get('uuid'), self.share.uuid)

    @patch("socialhome.users.tasks.exports.django_rq.enqueue", autospec=True)
    def test_notify(self, mock_enqueue):
        self.exporter.notify()
        self.assertEqual(mock_enqueue.call_count, 1)
        args, kwargs = mock_enqueue.call_args
        self.assertEqual(args[1], self.user.id)
