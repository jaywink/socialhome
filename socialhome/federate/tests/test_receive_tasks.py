# -*- coding: utf-8 -*-
from unittest.mock import patch

import pytest

from federation.tests.factories.entities import DiasporaPostFactory

from socialhome.content.models import Post
from socialhome.content.tests.factories import PostFactory
from socialhome.federate.tasks import receive_task, process_entities
from socialhome.users.tests.factories import ProfileFactory


@pytest.mark.usefixtures("db")
@patch("socialhome.federate.tasks.process_entities")
class TestReceivePublicTask(object):
    @patch("socialhome.federate.tasks.handle_receive", return_value=("sender", "diaspora", ["entity"]))
    @patch("socialhome.federate.tasks.get_sender_profile")
    def test_receive_public_task_runs(self, mock_get_user, mock_handle_receive, mock_process_entities):
        mock_get_user.return_value = ProfileFactory()
        receive_task("foobar")


@pytest.mark.usefixtures("db")
class TestProcessEntities(object):
    def test_post_is_created_from_entity(self):
        entity = DiasporaPostFactory()
        process_entities([entity], profile=ProfileFactory())
        Post.objects.get(guid=entity.guid)

    def test_post_is_updated_from_entity(self):
        entity = DiasporaPostFactory()
        PostFactory(guid=entity.guid)
        process_entities([entity], profile=ProfileFactory())
        post = Post.objects.get(guid=entity.guid)
        assert post.text == entity.raw_content
