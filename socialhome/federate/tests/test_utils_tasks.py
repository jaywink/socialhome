from unittest.mock import patch, Mock

import pytest
from federation.entities import base
from federation.tests.factories import entities
from test_plus import TestCase

from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory, LocalContentFactory
from socialhome.enums import Visibility
from socialhome.federate.utils.tasks import (
    process_entities, get_sender_profile, make_federable_entity, make_federable_retraction, process_entity_post,
    process_entity_retraction, sender_key_fetcher)
from socialhome.users.models import Profile
from socialhome.users.tests.factories import ProfileFactory, UserFactory


class TestProcessEntities(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestProcessEntities, cls).setUpTestData()
        cls.profile = Mock()
        cls.post = entities.PostFactory()
        cls.retraction = base.Retraction(handle=cls.post.handle, target_guid=cls.post.guid, entity_type="Post")

    @patch("socialhome.federate.utils.tasks.process_entity_post")
    def test_process_entity_post_is_called(self, mock_process):
        process_entities([self.post], profile=self.profile)
        mock_process.assert_called_once_with(self.post, self.profile)

    @patch("socialhome.federate.utils.tasks.process_entity_retraction")
    def test_process_entity_retraction_is_called(self, mock_process):
        process_entities([self.retraction], profile=self.profile)
        mock_process.assert_called_once_with(self.retraction, self.profile)

    @patch("socialhome.federate.utils.tasks.process_entity_post", side_effect=Exception)
    @patch("socialhome.federate.utils.tasks.logger.exception")
    def test_logger_is_called_on_process_exception(self, mock_process, mock_logger):
        process_entities([self.post], profile=self.profile)
        self.assertEqual(mock_logger.called, 1)


@pytest.mark.usefixtures("db")
class TestProcessEntityPost(object):
    def test_post_is_created_from_entity(self):
        entity = entities.PostFactory()
        process_entity_post(entity, ProfileFactory())
        Content.objects.get(guid=entity.guid)

    def test_entity_images_are_prefixed_to_post_text(self):
        entity = entities.PostFactory(
            _children=[
                base.Image(remote_path="foo", remote_name="bar"),
                base.Image(remote_path="zoo", remote_name="dee"),
            ],
        )
        process_entity_post(entity, ProfileFactory())
        content = Content.objects.get(guid=entity.guid)
        assert content.text.index("![](foobar) ![](zoodee) \n\n%s" % entity.raw_content) == 0

    def test_post_is_updated_from_entity(self):
        entity = entities.PostFactory()
        ContentFactory(guid=entity.guid)
        process_entity_post(entity, ProfileFactory())
        content = Content.objects.get(guid=entity.guid)
        assert content.text == entity.raw_content

    def test_post_text_fields_are_cleaned(self):
        entity = entities.PostFactory(
            raw_content="<script>alert('yup');</script>",
            provider_display_name="<script>alert('yup');</script>",
            guid="<script>alert('yup');</script>"
        )
        process_entity_post(entity, ProfileFactory())
        content = Content.objects.get(guid="alert('yup');")
        assert content.text == "&lt;script&gt;alert('yup');&lt;/script&gt;"
        assert content.service_label == "alert('yup');"


@pytest.mark.usefixtures("db")
class TestProcessEntityRetraction(TestCase):
    @patch("socialhome.federate.utils.tasks.logger.debug")
    def test_non_post_entity_types_are_skipped(self, mock_logger):
        process_entity_retraction(Mock(entity_type="foo"), Mock())
        mock_logger.assert_called_with("Ignoring retraction of entity_type %s", "foo")

    @patch("socialhome.federate.utils.tasks.logger.warning")
    def test_does_nothing_if_content_doesnt_exist(self, mock_logger):
        process_entity_retraction(Mock(entity_type="Post", target_guid="bar"), Mock())
        mock_logger.assert_called_with("Retracted content %s cannot be found", "bar")

    @patch("socialhome.federate.utils.tasks.logger.warning")
    def test_does_nothing_if_content_is_not_local(self, mock_logger):
        content = LocalContentFactory()
        process_entity_retraction(Mock(entity_type="Post", target_guid=content.guid), Mock())
        mock_logger.assert_called_with("Local content %s cannot be retracted by a remote retraction!", content)

    @patch("socialhome.federate.utils.tasks.logger.warning")
    def test_does_nothing_if_content_author_is_not_same_as_remote_profile(self, mock_logger):
        content = ContentFactory()
        remote_profile = Mock()
        process_entity_retraction(Mock(entity_type="Post", target_guid=content.guid), remote_profile)
        mock_logger.assert_called_with(
            "Content %s is not owned by remote retraction profile %s", content, remote_profile
        )

    def test_deletes_content(self):
        content = ContentFactory()
        process_entity_retraction(
            Mock(entity_type="Post", target_guid=content.guid, handle=content.author.handle),
            content.author
        )
        with self.assertRaises(Content.DoesNotExist):
            Content.objects.get(id=content.id)


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


@pytest.mark.usefixtures("db")
class TestMakeFederableRetraction(TestCase):
    def test_returns_entity(self):
        content = ContentFactory()
        entity = make_federable_retraction(content, content.author)
        self.assertEqual(entity.entity_type, "Post")
        self.assertEqual(entity.target_guid, content.guid)
        self.assertEqual(entity.handle, content.author.handle)

    @patch("socialhome.federate.utils.tasks.base.Retraction", side_effect=Exception)
    def test_returns_none_on_exception(self, mock_post):
        entity = make_federable_retraction(Mock(), Mock())
        self.assertIsNone(entity)


@pytest.mark.usefixtures("db")
class TestSenderKeyFetcher(TestCase):
    def test_local_profile_public_key_is_returned(self):
        profile = ProfileFactory()
        self.assertEqual(sender_key_fetcher(profile.handle), profile.rsa_public_key)

    @patch("socialhome.federate.utils.tasks.retrieve_remote_profile")
    @patch("socialhome.federate.utils.tasks.Profile.from_remote_profile")
    def test_remote_profile_public_key_is_returned(self, mock_from_remote, mock_retrieve):
        remote_profile = Mock(public_key="foo")
        mock_retrieve.return_value = remote_profile
        self.assertEqual(sender_key_fetcher("bar"), "foo")
        mock_retrieve.assert_called_once_with("bar")
        mock_from_remote.assert_called_once_with(remote_profile)

    @patch("socialhome.federate.utils.tasks.retrieve_remote_profile", return_value=None)
    @patch("socialhome.federate.utils.tasks.logger.warning")
    def test_nonexisting_remote_profile_is_logged(self, mock_logger, mock_retrieve):
        self.assertEqual(sender_key_fetcher("bar"), None)
        mock_logger.assert_called_once_with("Remote profile %s for sender key not found locally or remotely.", "bar")
