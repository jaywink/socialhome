from unittest.mock import patch, Mock

import pytest
from test_plus import TestCase

from federation.entities import base
from federation.tests.factories import entities

from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory
from socialhome.enums import Visibility
from socialhome.federate.utils.tasks import process_entities, get_sender_profile, make_federable_entity
from socialhome.users.models import Profile
from socialhome.users.tests.factories import ProfileFactory


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

    @patch("socialhome.federate.utils.tasks.retrieve_remote_profile")
    def test_fetches_remote_profile_if_not_found(self, mock_retrieve):
        mock_retrieve.return_value = entities.ProfileFactory(
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

    @patch("socialhome.federate.utils.tasks.retrieve_remote_profile")
    def test_returns_none_if_no_remote_profile_found(self, mock_retrieve):
        mock_retrieve.return_value = None
        assert not get_sender_profile("foo@example.com")

    @patch("socialhome.federate.utils.tasks.retrieve_remote_profile")
    def test_cleans_text_fields_in_profile(self, mock_retrieve):
        mock_retrieve.return_value = entities.ProfileFactory(
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


@pytest.mark.usefixtures("db")
class TestMakeFederableEntity(TestCase):
    def test_returns_entity(self):
        content = ContentFactory()
        entity = make_federable_entity(content)
        self.assertEqual(entity.raw_content, content.text)
        self.assertEqual(entity.guid, content.guid)
        self.assertEqual(entity.handle, content.author.handle)
        self.assertEqual(entity.public, True)
        self.assertEqual(entity.provider_display_name, "Socialhome")
        self.assertEqual(entity.created_at, content.effective_created)

    @patch("socialhome.federate.utils.tasks.base.Post", side_effect=Exception)
    def test_returns_none_on_exception(self, mock_post):
        entity = make_federable_entity(Mock())
        self.assertIsNone(entity)
