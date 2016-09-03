from unittest.mock import patch

import pytest

from socialhome.federate.tasks import receive_task
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
        assert receive_task("foobar") == None
        mock_process_entities.assert_not_called()

    @patch("socialhome.federate.tasks.handle_receive", return_value=("sender", "diaspora", []))
    @patch("socialhome.federate.tasks.get_sender_profile")
    def test_receive_task_returns_none_on_no_entities(self, mock_get_sender, mock_handle_receive,
                                                      mock_process_entities):
        assert receive_task("foobar") == None
        mock_process_entities.assert_not_called()
