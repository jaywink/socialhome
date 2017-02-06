import json
from unittest.mock import patch, Mock

import pytest
from test_plus import TestCase

from socialhome.content.tests.factories import ContentFactory
from socialhome.federate.tasks import send_content, send_content_retraction
from socialhome.users.tests.factories import UserFactory


@pytest.mark.usefixtures("db")
class TestNotifyListeners(TestCase):
    @patch("socialhome.content.signals.StreamConsumer")
    def test_content_save_calls_streamconsumer_group_send(self, mock_consumer):
        mock_consumer.group_send = Mock()
        content = ContentFactory()
        mock_consumer.group_send.assert_called_once_with(
            "streams_public", json.dumps({"event": "new", "id": content.id})
        )
        mock_consumer.group_send.reset_mock()
        # Update shouldn't cause a group send
        content.text = "foo"
        content.save()
        self.assertFalse(mock_consumer.group_send.called)


@pytest.mark.usefixtures("db")
class TestFederateContent(TestCase):
    @patch("socialhome.content.signals.django_rq.enqueue")
    def test_non_local_content_does_not_get_sent(self, mock_send):
        ContentFactory()
        mock_send.assert_not_called()

    @patch("socialhome.content.signals.django_rq.enqueue")
    def test_local_content_gets_sent(self, mock_send):
        user = UserFactory()
        content = ContentFactory(author=user.profile)
        self.assertTrue(content.is_local)
        mock_send.assert_called_once_with(send_content, content.id)

    @patch("socialhome.content.signals.django_rq.enqueue", side_effect=Exception)
    @patch("socialhome.content.signals.logger.exception")
    def test_exception_calls_logger(self, mock_logger, mock_send):
        user = UserFactory()
        ContentFactory(author=user.profile)
        self.assertTrue(mock_logger.called)


@pytest.mark.usefixtures("db")
class TestFederateContentRetraction(TestCase):
    @patch("socialhome.content.signals.django_rq.enqueue")
    def test_non_local_content_retraction_does_not_get_sent(self, mock_send):
        content = ContentFactory()
        content.delete()
        mock_send.assert_not_called()

    @patch("socialhome.content.signals.django_rq.enqueue")
    def test_local_content_retraction_gets_sent(self, mock_send):
        user = UserFactory()
        content = ContentFactory(author=user.profile)
        self.assertTrue(content.is_local)
        mock_send.reset_mock()
        content_id = content.id
        content.delete()
        mock_send.assert_called_once_with(send_content_retraction, content_id, content.author_id)

    @patch("socialhome.content.signals.django_rq.enqueue", side_effect=Exception)
    @patch("socialhome.content.signals.logger.exception")
    def test_exception_calls_logger(self, mock_logger, mock_send):
        user = UserFactory()
        content = ContentFactory(author=user.profile)
        content.delete()
        self.assertTrue(mock_logger.called)


@pytest.mark.usefixtures("db")
class TestFetchPreview(TestCase):
    @patch("socialhome.content.signals.fetch_content_preview")
    def test_fetch_content_preview_called(self, fetch):
        content = ContentFactory()
        fetch.assert_called_once_with(content)

    @patch("socialhome.content.signals.fetch_content_preview", side_effect=Exception)
    @patch("socialhome.content.signals.logger.exception")
    def test_fetch_content_preview_exception_logger_called(self, logger, fetch):
        ContentFactory()
        self.assertTrue(logger.called)


@pytest.mark.usefixtures("db")
class TestExtractTags(TestCase):
    def test_extract_content_called(self):
        content = ContentFactory()
        content.extract_tags = Mock()
        content.save()
        content.extract_tags.assert_called_once_with()

    @patch("socialhome.content.signals.logger.exception")
    def test_extract_content_exception_logger_called(self, logger):
        content = ContentFactory()
        content.extract_tags = Mock(side_effect=Exception)
        content.save()
        self.assertTrue(logger.called)
