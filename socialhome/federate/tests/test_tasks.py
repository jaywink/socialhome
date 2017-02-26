from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import override_settings
from test_plus import TestCase

from socialhome.content.tests.factories import ContentFactory
from socialhome.enums import Visibility
from socialhome.federate.tasks import receive_task, send_content, send_content_retraction
from socialhome.users.tests.factories import ProfileFactory


@pytest.mark.usefixtures("db")
@patch("socialhome.federate.tasks.process_entities")
class TestReceiveTask(object):
    @patch("socialhome.federate.tasks.handle_receive", return_value=("sender", "diaspora", ["entity"]))
    @patch("socialhome.federate.tasks.get_sender_profile")
    def test_receive_task_runs(self, mock_get_sender, mock_handle_receive, mock_process_entities):
        profile = ProfileFactory()
        mock_get_sender.return_value = profile
        receive_task("foobar")
        mock_process_entities.assert_called_with(["entity"], profile=profile)

    @patch("socialhome.federate.tasks.handle_receive", return_value=("sender", "diaspora", ["entity"]))
    @patch("socialhome.federate.tasks.get_sender_profile")
    def test_receive_task_returns_none_on_no_sender_profile(self, mock_get_sender, mock_handle_receive,
                                                            mock_process_entities):
        mock_get_sender.return_value = None
        assert receive_task("foobar") is None
        mock_process_entities.assert_not_called()

    @patch("socialhome.federate.tasks.handle_receive", return_value=("sender", "diaspora", []))
    @patch("socialhome.federate.tasks.get_sender_profile")
    def test_receive_task_returns_none_on_no_entities(self, mock_get_sender, mock_handle_receive,
                                                      mock_process_entities):
        assert receive_task("foobar") is None
        mock_process_entities.assert_not_called()


@pytest.mark.usefixtures("db")
class TestSendContent(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestSendContent, cls).setUpTestData()
        cls.limited_content = ContentFactory(visibility=Visibility.LIMITED)
        cls.public_content = ContentFactory(visibility=Visibility.PUBLIC)

    @patch("socialhome.federate.tasks.make_federable_entity", return_value=None)
    def test_only_public_content_calls_make_federable_entity(self, mock_maker):
        send_content(self.limited_content.id)
        mock_maker.assert_not_called()
        send_content(self.public_content.id)
        mock_maker.assert_called_once_with(self.public_content)

    @patch("socialhome.federate.tasks.handle_create_payload")
    @patch("socialhome.federate.tasks.send_document", return_value=None)
    @patch("socialhome.federate.tasks.make_federable_entity", return_value="entity")
    def test_handle_create_payload_is_called(self, mock_maker, mock_sender, mock_handler):
        send_content(self.public_content.id)
        mock_handler.assert_called_once_with("entity", self.public_content.author)

    @patch("socialhome.federate.tasks.handle_create_payload", return_value="payload")
    @patch("socialhome.federate.tasks.send_document", return_value=None)
    def test_send_document_is_called(self, mock_sender, mock_payloader):
        send_content(self.public_content.id)
        url = "https://%s/receive/public" % settings.SOCIALHOME_RELAY_DOMAIN
        mock_sender.assert_called_once_with(url, "payload")

    @patch("socialhome.federate.tasks.make_federable_entity", return_value=None)
    @patch("socialhome.federate.tasks.logger.warning")
    def test_warning_is_logged_on_no_entity(self, mock_logger, mock_maker):
        send_content(self.public_content.id)
        self.assertTrue(mock_logger.called)

    @override_settings(DEBUG=True)
    @patch("socialhome.federate.tasks.handle_create_payload")
    def test_content_not_sent_in_debug_mode(self, mock_payload):
        send_content(self.public_content.id)
        mock_payload.assert_not_called()


@pytest.mark.usefixtures("db")
class TestSendContentRetraction(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestSendContentRetraction, cls).setUpTestData()
        cls.limited_content = ContentFactory(visibility=Visibility.LIMITED)
        cls.public_content = ContentFactory(visibility=Visibility.PUBLIC)

    @patch("socialhome.federate.tasks.make_federable_retraction", return_value=None)
    def test_only_public_content_calls_make_federable_entity(self, mock_maker):
        send_content_retraction(self.limited_content, self.limited_content.author_id)
        mock_maker.assert_not_called()
        send_content_retraction(self.public_content, self.public_content.author_id)
        mock_maker.assert_called_once_with(self.public_content, self.public_content.author)

    @patch("socialhome.federate.tasks.handle_create_payload")
    @patch("socialhome.federate.tasks.send_document", return_value=None)
    @patch("socialhome.federate.tasks.make_federable_retraction", return_value="entity")
    def test_handle_create_payload_is_called(self, mock_maker, mock_sender, mock_handler):
        send_content_retraction(self.public_content, self.public_content.author_id)
        mock_handler.assert_called_once_with("entity", self.public_content.author)

    @patch("socialhome.federate.tasks.handle_create_payload", return_value="payload")
    @patch("socialhome.federate.tasks.send_document", return_value=None)
    def test_send_document_is_called(self, mock_sender, mock_payloader):
        send_content_retraction(self.public_content, self.public_content.author_id)
        url = "https://%s/receive/public" % settings.SOCIALHOME_RELAY_DOMAIN
        mock_sender.assert_called_once_with(url, "payload")

    @patch("socialhome.federate.tasks.make_federable_retraction", return_value=None)
    @patch("socialhome.federate.tasks.logger.warning")
    def test_warning_is_logged_on_no_entity(self, mock_logger, mock_maker):
        send_content_retraction(self.public_content, self.public_content.author_id)
        self.assertTrue(mock_logger.called)

    @override_settings(DEBUG=True)
    @patch("socialhome.federate.tasks.handle_create_payload")
    def test_content_not_sent_in_debug_mode(self, mock_payload):
        send_content_retraction(self.public_content, self.public_content.author_id)
        mock_payload.assert_not_called()
