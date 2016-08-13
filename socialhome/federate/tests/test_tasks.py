# -*- coding: utf-8 -*-
from unittest.mock import patch

import pytest
from federation.entities import base
from federation.tests.factories import entities

from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory
from socialhome.enums import Visibility
from socialhome.federate.tasks import receive_task, process_entities, get_sender_profile
from socialhome.users.models import Profile
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


@pytest.mark.usefixtures("db")
class TestProcessEntities(object):
    def test_post_is_created_from_entity(self):
        entity = entities.PostFactory()
        process_entities([entity], profile=ProfileFactory())
        Content.objects.get(guid=entity.guid)

    def test_post_is_updated_from_entity(self):
        entity = entities.PostFactory()
        ContentFactory(guid=entity.guid)
        process_entities([entity], profile=ProfileFactory())
        content = Content.objects.get(guid=entity.guid)
        assert content.text == entity.raw_content

    def test_post_text_fields_are_cleaned(self):
        entity = entities.PostFactory(
            raw_content="<script>alert('yup');</script>",
            provider_display_name="<script>alert('yup');</script>",
            guid="<script>alert('yup');</script>"
        )
        process_entities([entity], profile=ProfileFactory())
        content = Content.objects.get(guid="alert('yup');")
        assert content.text == "&lt;script&gt;alert('yup');&lt;/script&gt;"
        assert content.service_label == "alert('yup');"


@pytest.mark.usefixtures("db")
class TestGetSenderProfile(object):
    def test_returns_existing_profile(self):
        profile = ProfileFactory(handle="foo@example.com")
        assert get_sender_profile("foo@example.com") == profile

    @patch("socialhome.federate.tasks.retrieve_remote_profile")
    def test_fetches_remote_profile_if_not_found(self, mock_retrieve):
        # TODO: use ProfileFactory from Social-Federation once available
        mock_retrieve.return_value = base.Profile(
            name="foobar", raw_content="barfoo", public_key="xyz",
            handle="foo@example.com", guid="123456"
        )
        sender_profile = get_sender_profile("foo@example.com")
        assert isinstance(sender_profile, Profile)
        assert sender_profile.name == "foobar"
        assert sender_profile.guid == "123456"
        assert sender_profile.handle == "foo@example.com"
        assert sender_profile.visibility == Visibility.LIMITED
        assert sender_profile.rsa_public_key == "xyz"
        assert not sender_profile.rsa_private_key

    @patch("socialhome.federate.tasks.retrieve_remote_profile")
    def test_returns_none_if_no_remote_profile_found(self, mock_retrieve):
        mock_retrieve.return_value = None
        assert not get_sender_profile("foo@example.com")

    @patch("socialhome.federate.tasks.retrieve_remote_profile")
    def test_cleans_text_fields_in_profile(self, mock_retrieve):
        # TODO: use ProfileFactory from Social-Federation once available
        mock_retrieve.return_value = base.Profile(
            name="<script>alert('yup');</script>", raw_content="<script>alert('yup');</script>",
            public_key="<script>alert('yup');</script>",
            handle="foo@example.com", guid="<script>alert('yup');</script>",
            image_urls={
                "small": "<script>alert('yup');</script>",
                "medium": "<script>alert('yup');</script>",
                "large": "<script>alert('yup');</script>",
            },
            location="<script>alert('yup');</script>",
        )
        sender_profile = get_sender_profile("foo@example.com")
        assert isinstance(sender_profile, Profile)
        assert sender_profile.name == "alert('yup');"
        assert sender_profile.guid == "alert('yup');"
        assert sender_profile.rsa_public_key == "alert('yup');"
        assert sender_profile.image_url_small == "alert('yup');"
        assert sender_profile.image_url_medium == "alert('yup');"
        assert sender_profile.image_url_large == "alert('yup');"
        assert sender_profile.location == "alert('yup');"
