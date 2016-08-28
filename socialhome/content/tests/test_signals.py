import json
from unittest.mock import patch, Mock

import pytest
from test_plus import TestCase

from socialhome.content.tests.factories import ContentFactory


@pytest.mark.usefixtures("db")
class TestContentModel(TestCase):
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
