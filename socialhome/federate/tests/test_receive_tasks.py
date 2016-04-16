# -*- coding: utf-8 -*-
from unittest.mock import patch

import pytest

from federation.tests.factories.entities import DiasporaPostFactory

from socialhome.content.models import Post
from socialhome.content.tests.factories import PostFactory
from socialhome.federate.tasks import receive_public_task, process_entities


@pytest.mark.usefixtures("db")
@patch("socialhome.federate.tasks.process_entities")
class TestReceivePublicTask(object):
    @patch("socialhome.federate.tasks.handle_receive", return_value=("sender", "diaspora", ["entity"]))
    def test_receive_public_task_runs(self, mock_handle_receive, mock_process_entities):
        receive_public_task("foobar")

    @patch("socialhome.federate.tasks.handle_receive", return_value=("sender", "smtp", ["entity"]))
    def test_receive_public_task_ignores_non_diaspora_protocol(self, mock_handle_receive, mock_process_entities):
        receive_public_task("foobar")
        assert not mock_process_entities.called


@pytest.mark.usefixtures("db")
class TestProcessEntities(object):
    def test_post_is_created_from_entity(self):
        entity = DiasporaPostFactory()
        process_entities([entity])
        Post.objects.get(guid=entity.guid)

    def test_post_is_updated_from_entity(self):
        entity = DiasporaPostFactory()
        PostFactory(guid=entity.guid)
        process_entities([entity])
        post = Post.objects.get(guid=entity.guid)
        assert post.text == entity.raw_content
