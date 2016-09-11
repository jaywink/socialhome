import json
from unittest.mock import patch, Mock

import pytest
from test_plus import TestCase

from socialhome.content.tests.factories import ContentFactory
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
@patch("socialhome.content.signals.send_content.delay")
class TestFederateContent(TestCase):
    def test_non_local_content_does_not_get_sent(self, mock_send):
        ContentFactory()
        mock_send.assert_not_called()

    def test_local_content_gets_sent(self, mock_send):
        user = UserFactory()
        content = ContentFactory(author=user.profile)
        self.assertTrue(content.is_local)
        mock_send.assert_called_once_with(content)
