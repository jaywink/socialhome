from unittest.mock import patch, Mock, call
from uuid import uuid4

from django.db import IntegrityError
from federation.entities import base
from federation.tests.factories import entities

from socialhome.content.enums import ContentType
from socialhome.content.models import Content
from socialhome.content.tests.factories import ContentFactory, LocalContentFactory
from socialhome.enums import Visibility
from socialhome.federate.tasks import forward_relayable
from socialhome.federate.utils.tasks import (
    process_entities, get_sender_profile, make_federable_content, make_federable_retraction, process_entity_post,
    process_entity_retraction, sender_key_fetcher, process_entity_comment, process_entity_follow,
    process_entity_relationship, make_federable_profile, process_entity_share)
from socialhome.notifications.tasks import send_follow_notification
from socialhome.tests.utils import SocialhomeTestCase, SocialhomeTransactionTestCase
from socialhome.users.models import Profile
from socialhome.users.tests.factories import (
    ProfileFactory, UserFactory, BaseProfileFactory, BaseShareFactory, PublicProfileFactory,
)


class TestProcessEntities(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.post = entities.PostFactory()
        cls.comment = base.Comment()
        cls.retraction = base.Retraction()
        cls.relationship = base.Relationship()
        cls.follow = base.Follow()
        cls.profile = BaseProfileFactory()
        cls.share = BaseShareFactory()

    @patch("socialhome.federate.utils.tasks.process_entity_post")
    @patch("socialhome.federate.utils.tasks.get_sender_profile", return_value="profile")
    def test_process_entity_post_is_called(self, mock_sender, mock_process):
        process_entities([self.post])
        mock_process.assert_called_once_with(self.post, "profile")

    @patch("socialhome.federate.utils.tasks.process_entity_retraction")
    @patch("socialhome.federate.utils.tasks.get_sender_profile", return_value="profile")
    def test_process_entity_retraction_is_called(self, mock_sender, mock_process):
        process_entities([self.retraction])
        mock_process.assert_called_once_with(self.retraction, "profile")

    @patch("socialhome.federate.utils.tasks.process_entity_comment")
    @patch("socialhome.federate.utils.tasks.get_sender_profile", return_value="profile")
    def test_process_entity_comment_is_called(self, mock_sender, mock_process):
        process_entities([self.comment])
        mock_process.assert_called_once_with(self.comment, "profile")

    @patch("socialhome.federate.utils.tasks.process_entity_relationship")
    @patch("socialhome.federate.utils.tasks.get_sender_profile", return_value="profile")
    def test_process_entity_relationship_is_called(self, mock_sender, mock_process):
        process_entities([self.relationship])
        mock_process.assert_called_once_with(self.relationship, "profile")

    @patch("socialhome.federate.utils.tasks.process_entity_follow")
    @patch("socialhome.federate.utils.tasks.get_sender_profile", return_value="profile")
    def test_process_entity_follow_is_called(self, mock_sender, mock_process):
        process_entities([self.follow])
        mock_process.assert_called_once_with(self.follow, "profile")

    @patch("socialhome.federate.utils.tasks.Profile.from_remote_profile")
    @patch("socialhome.federate.utils.tasks.get_sender_profile", return_value="profile")
    def test_process_entity_profile_is_called(self, mock_sender, mock_from):
        process_entities([self.profile])
        mock_from.assert_called_once_with(self.profile)

    @patch("socialhome.federate.utils.tasks.process_entity_share")
    @patch("socialhome.federate.utils.tasks.get_sender_profile", return_value="profile")
    def test_process_entity_share_is_called(self, mock_sender, mock_process):
        process_entities([self.share])
        mock_process.assert_called_once_with(self.share, "profile")

    @patch("socialhome.federate.utils.tasks.process_entity_post", side_effect=Exception)
    @patch("socialhome.federate.utils.tasks.logger.exception")
    @patch("socialhome.federate.utils.tasks.get_sender_profile", return_value="profile")
    def test_logger_is_called_on_process_exception(self, mock_sender, mock_process, mock_logger):
        process_entities([self.post])
        self.assertEqual(mock_logger.called, 1)


class TestProcessEntityPost(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.local_content = LocalContentFactory()

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
        author = ProfileFactory(handle=entity.handle)
        ContentFactory(guid=entity.guid, author=author)
        process_entity_post(entity, author)
        content = Content.objects.get(guid=entity.guid)
        self.assertEqual(content.text, entity.raw_content)

        # Don't allow updating if the author is different
        invalid_entity = entities.PostFactory(guid=entity.guid)
        process_entity_post(invalid_entity, ProfileFactory(handle=invalid_entity.handle))
        content.refresh_from_db()
        self.assertEqual(content.text, entity.raw_content)
        self.assertEqual(content.author, author)

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

    @patch("socialhome.federate.utils.tasks.Content.objects.update_or_create", return_value=(None, None))
    def test_local_content_is_skipped(self, mock_update):
        entity = entities.PostFactory(guid=self.local_content.guid)
        process_entity_post(entity, ProfileFactory())
        self.assertFalse(mock_update.called)


class TestProcessEntityComment(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.content = ContentFactory()

    def setUp(self):
        super().setUp()
        self.comment = base.Comment(guid="guid"*4, target_guid=self.content.guid, raw_content="foobar",
                                    handle="thor@example.com")

    def test_reply_is_created_from_entity(self):
        process_entity_comment(self.comment, ProfileFactory())
        Content.objects.get(guid=self.comment.guid, parent=self.content)

    def test_entity_images_are_prefixed_to_post_text(self):
        self.comment._children = [
            base.Image(remote_path="foo", remote_name="bar"),
            base.Image(remote_path="zoo", remote_name="dee"),
        ]
        process_entity_comment(self.comment, ProfileFactory())
        content = Content.objects.get(guid=self.comment.guid, parent=self.content)
        self.assertEqual(content.text.index("![](foobar) ![](zoodee) \n\n%s" % self.comment.raw_content), 0)

    def test_reply_is_updated_from_entity(self):
        author = ProfileFactory(handle=self.comment.handle)
        ContentFactory(guid=self.comment.guid, author=author)
        process_entity_comment(self.comment, author)
        content = Content.objects.get(guid=self.comment.guid, parent=self.content)
        self.assertEqual(content.text, self.comment.raw_content)

        # Don't allow updating if the author is different
        invalid_entity = base.Comment(guid=self.comment.guid, raw_content="barfoo", handle="loki@example.com",
                                      target_guid=self.content.guid)
        process_entity_comment(invalid_entity, ProfileFactory(handle=invalid_entity.handle))
        content.refresh_from_db()
        self.assertEqual(content.text, self.comment.raw_content)
        self.assertEqual(content.author, author)

        # Don't allow changing parent
        invalid_entity = base.Comment(guid=self.comment.guid, raw_content="barfoo", handle="thor@example.com",
                                      target_guid=ContentFactory().guid)
        process_entity_comment(invalid_entity, author)
        content.refresh_from_db()
        self.assertEqual(content.text, self.comment.raw_content)
        self.assertEqual(content.author, author)

    def test_reply_text_fields_are_cleaned(self):
        self.comment.raw_content = "<script>alert('yup');</script>"
        process_entity_comment(self.comment, ProfileFactory())
        content = Content.objects.get(guid=self.comment.guid, parent=self.content)
        self.assertEqual(content.text, "&lt;script&gt;alert('yup');&lt;/script&gt;")

    @patch("socialhome.federate.utils.tasks.django_rq.enqueue")
    def test_does_not_forwards_relayable_if_not_local_content(self, mock_rq):
        process_entity_comment(self.comment, ProfileFactory())
        Content.objects.get(guid=self.comment.guid, parent=self.content)
        self.assertFalse(mock_rq.called)

    @patch("socialhome.federate.utils.tasks.django_rq.enqueue")
    def test_forwards_relayable_if_local_content(self, mock_rq):
        user = UserFactory()
        self.content.author = user.profile
        self.content.save()
        self.content.refresh_from_db()
        mock_rq.reset_mock()
        process_entity_comment(self.comment, ProfileFactory())
        Content.objects.get(guid=self.comment.guid, parent=self.content)
        call_args = [
            call(forward_relayable, self.comment, self.content.id),
        ]
        self.assertEqual(mock_rq.call_args_list, call_args)

    @patch("socialhome.federate.utils.tasks.Content.objects.update_or_create", return_value=(None, None))
    def test_local_reply_is_skipped(self, mock_update):
        user = UserFactory()
        ContentFactory(guid=self.comment.guid, author=user.profile)
        process_entity_comment(self.comment, ProfileFactory())
        self.assertFalse(mock_update.called)


class TestProcessEntityRetraction(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.content = ContentFactory()
        cls.local_content = LocalContentFactory()
        cls.create_local_and_remote_user()

    def setUp(self):
        super().setUp()
        self.content.refresh_from_db()

    @patch("socialhome.federate.utils.tasks.logger.debug")
    def test_non_post_entity_types_are_skipped(self, mock_logger):
        process_entity_retraction(Mock(entity_type="foo"), Mock())
        mock_logger.assert_called_with("Ignoring retraction of entity_type %s", "foo")

    @patch("socialhome.federate.utils.tasks.logger.warning")
    def test_does_nothing_if_content_doesnt_exist(self, mock_logger):
        process_entity_retraction(Mock(entity_type="Post", target_guid="bar"), Mock())
        mock_logger.assert_called_with("Retracted remote content %s cannot be found", "bar")

    @patch("socialhome.federate.utils.tasks.logger.warning")
    def test_does_nothing_if_content_is_not_local(self, mock_logger):
        process_entity_retraction(Mock(entity_type="Post", target_guid=self.local_content.guid), Mock())
        mock_logger.assert_called_with(
            "Retracted remote content %s cannot be found", self.local_content.guid,
        )

    @patch("socialhome.federate.utils.tasks.logger.warning")
    def test_does_nothing_if_content_author_is_not_same_as_remote_profile(self, mock_logger):
        remote_profile = Mock()
        process_entity_retraction(Mock(entity_type="Post", target_guid=self.content.guid), remote_profile)
        mock_logger.assert_called_with(
            "Content %s is not owned by remote retraction profile %s", self.content, remote_profile
        )

    def test_deletes_content(self):
        process_entity_retraction(
            Mock(entity_type="Post", target_guid=self.content.guid, handle=self.content.author.handle),
            self.content.author
        )
        with self.assertRaises(Content.DoesNotExist):
            Content.objects.get(id=self.content.id)

    def test_removes_follower(self):
        self.remote_profile.following.add(self.profile)
        process_entity_retraction(
            base.Retraction(entity_type="Profile", _receiving_guid=self.profile.guid),
            self.remote_profile,
        )
        self.assertEqual(self.remote_profile.following.count(), 0)


class TestProcessEntityFollow(SocialhomeTransactionTestCase):
    def setUp(self):
        super().setUp()
        self.create_local_and_remote_user()

    def test_follower_added_on_following_true(self):
        process_entity_follow(base.Follow(target_handle=self.profile.handle, following=True), self.remote_profile)
        self.assertEqual(self.remote_profile.following.count(), 1)
        self.assertEqual(self.remote_profile.following.first().handle, self.profile.handle)

    def test_follower_removed_on_following_false(self):
        self.remote_profile.following.add(self.profile)
        process_entity_follow(base.Follow(target_handle=self.profile.handle, following=False), self.remote_profile)
        self.assertEqual(self.remote_profile.following.count(), 0)

    @patch("socialhome.users.signals.django_rq.enqueue")
    def test_follower_added_sends_a_notification(self, mock_enqueue):
        process_entity_follow(base.Follow(target_handle=self.profile.handle, following=True), self.remote_profile)
        mock_enqueue.assert_called_once_with(send_follow_notification, self.remote_profile.id, self.profile.id)


class TestProcessEntityRelationship(SocialhomeTransactionTestCase):
    def setUp(self):
        super().setUp()
        self.create_local_and_remote_user()

    def test_follower_added_on_following(self):
        process_entity_relationship(
            base.Relationship(target_handle=self.profile.handle, relationship="following"), self.remote_profile,
        )
        self.assertEqual(self.remote_profile.following.count(), 1)
        self.assertEqual(self.remote_profile.following.first().handle, self.profile.handle)

    def test_follower_not_added_on_not_following(self):
        process_entity_relationship(
            base.Relationship(target_handle=self.profile.handle, relationship="sharing"), self.remote_profile,
        )
        self.assertEqual(self.remote_profile.following.count(), 0)

    @patch("socialhome.users.signals.django_rq.enqueue")
    def test_follower_added_sends_a_notification(self, mock_enqueue):
        process_entity_relationship(
            base.Relationship(target_handle=self.profile.handle, relationship="following"), self.remote_profile,
        )
        mock_enqueue.assert_called_once_with(send_follow_notification, self.remote_profile.id, self.profile.id)


class TestProcessEntityShare(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.local_content = LocalContentFactory()
        cls.local_content2 = LocalContentFactory(guid=str(uuid4()))
        cls.remote_profile2 = PublicProfileFactory()

    def test_share_is_created(self):
        entity = base.Share(
            guid=str(uuid4()), handle=self.remote_profile.handle, target_guid=self.local_content.guid,
            target_handle=self.local_content.author.handle, public=True,
        )
        process_entity_share(entity, self.remote_profile)
        share = Content.objects.get(guid=entity.guid, share_of=self.local_content)
        self.assertEqual(share.text, "")
        self.assertEqual(share.author, self.remote_profile)
        self.assertEqual(share.visibility, Visibility.PUBLIC)
        self.assertEqual(share.service_label, "")
        self.assertEqual(share.guid, entity.guid)

        # Update
        entity.raw_content = "now we have text"
        process_entity_share(entity, self.remote_profile)
        share.refresh_from_db()
        self.assertEqual(share.text, "now we have text")

    @patch("socialhome.federate.utils.tasks.retrieve_remote_content", autospec=True, return_value=None)
    def test_share_is_not_created_if_no_target_found(self, mock_retrieve):
        entity = base.Share(
            guid=str(uuid4()), handle=self.remote_profile.handle, target_guid="notexistingguid",
            target_handle=self.local_content.author.handle, public=True,
        )
        process_entity_share(entity, self.remote_profile)
        self.assertFalse(Content.objects.filter(guid=entity.guid, share_of=self.local_content).exists())

    def test_share_is_not_created_if_target_handle_and_local_owner_differ(self):
        entity = base.Share(
            guid=str(uuid4()), handle=self.remote_profile.handle, target_guid=self.local_content.guid,
            target_handle="someoneelse@example.com", public=True,
        )
        process_entity_share(entity, self.remote_profile)
        self.assertFalse(Content.objects.filter(guid=entity.guid, share_of=self.local_content).exists())

    def test_share_cant_hijack_local_content(self):
        entity = base.Share(
            guid=self.local_content2.guid, handle=self.local_content2.author.handle,
            target_guid=self.local_content.guid, target_handle=self.local_content.author.handle, public=True,
            raw_content="this should never get saved",
        )
        current_text = self.local_content2.text
        with self.assertRaises(IntegrityError):
            process_entity_share(entity, self.remote_profile)
        self.local_content2.refresh_from_db()
        self.assertIsNone(self.local_content2.share_of)
        self.assertEqual(self.local_content2.text, current_text)

    @patch("socialhome.federate.utils.tasks.retrieve_remote_content", autospec=True)
    def test_share_target_is_fetched_if_no_target_found(self, mock_retrieve):
        entity = base.Share(
            guid=str(uuid4()), handle=self.remote_profile.handle, target_guid="notexistingguid",
            target_handle=self.remote_profile2.handle, public=True,
        )
        mock_retrieve.return_value = entities.PostFactory(
            guid=entity.target_guid, handle=self.remote_profile2.handle,
        )
        process_entity_share(entity, self.remote_profile)
        mock_retrieve.assert_called_once_with(entity.target_id, sender_key_fetcher=sender_key_fetcher)
        self.assertTrue(Content.objects.filter(guid=entity.target_guid, content_type=ContentType.CONTENT).exists())
        self.assertTrue(
            Content.objects.filter(
                guid=entity.guid, share_of__guid=entity.target_guid, content_type=ContentType.SHARE
            ).exists()
        )


class TestGetSenderProfile(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()

    def test_returns_existing_profile(self):
        self.assertEqual(get_sender_profile(self.remote_profile.handle), self.remote_profile)

    def test_returns_none_on_existing_local_profile(self):
        self.assertIsNone(get_sender_profile(self.profile.handle))

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


class TestMakeFederableContent(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.content = ContentFactory(visibility=Visibility.PUBLIC)
        cls.reply = ContentFactory(parent=cls.content, visibility=Visibility.PUBLIC)
        cls.share = ContentFactory(share_of=cls.content, visibility=Visibility.PUBLIC)

    def test_content_returns_entity(self):
        entity = make_federable_content(self.content)
        self.assertTrue(isinstance(entity, base.Post))
        self.assertEqual(entity.raw_content, self.content.text)
        self.assertEqual(entity.guid, self.content.guid)
        self.assertEqual(entity.handle, self.content.author.handle)
        self.assertEqual(entity.public, True)
        self.assertEqual(entity.provider_display_name, "Socialhome")
        self.assertEqual(entity.created_at, self.content.effective_modified)

        self.content.visibility = Visibility.LIMITED
        entity = make_federable_content(self.content)
        self.assertEqual(entity.public, False)

        self.content.visibility = Visibility.SELF
        entity = make_federable_content(self.content)
        self.assertEqual(entity.public, False)

        self.content.visibility = Visibility.SITE
        entity = make_federable_content(self.content)
        self.assertEqual(entity.public, False)

    def test_reply_returns_entity(self):
        entity = make_federable_content(self.reply)
        self.assertTrue(isinstance(entity, base.Comment))
        self.assertEqual(entity.raw_content, self.reply.text)
        self.assertEqual(entity.guid, self.reply.guid)
        self.assertEqual(entity.target_guid, self.reply.parent.guid)
        self.assertEqual(entity.handle, self.reply.author.handle)
        self.assertEqual(entity.created_at, self.reply.effective_modified)

    def test_share_returns_entity(self):
        entity = make_federable_content(self.share)
        self.assertTrue(isinstance(entity, base.Share))
        self.assertEqual(entity.raw_content, self.share.text)
        self.assertEqual(entity.guid, self.share.guid)
        self.assertEqual(entity.target_guid, self.share.share_of.guid)
        self.assertEqual(entity.handle, self.share.author.handle)
        self.assertEqual(entity.target_handle, self.share.share_of.author.handle)
        self.assertEqual(entity.public, True)
        self.assertEqual(entity.provider_display_name, "Socialhome")
        self.assertEqual(entity.created_at, self.share.effective_modified)

        self.content.visibility = Visibility.LIMITED
        entity = make_federable_content(self.content)
        self.assertEqual(entity.public, False)

        self.content.visibility = Visibility.SELF
        entity = make_federable_content(self.content)
        self.assertEqual(entity.public, False)

        self.content.visibility = Visibility.SITE
        entity = make_federable_content(self.content)
        self.assertEqual(entity.public, False)

    @patch("socialhome.federate.utils.tasks.base.Post", side_effect=Exception)
    def test_returns_none_on_exception(self, mock_post):
        mock_post = Mock()
        mock_post.parent = False
        entity = make_federable_content(mock_post)
        self.assertIsNone(entity)


class TestMakeFederableRetraction(SocialhomeTestCase):
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


class TestMakeFederableProfile(SocialhomeTestCase):
    def test_make_federable_profile(self):
        profile = ProfileFactory(visibility=Visibility.SELF)
        entity = make_federable_profile(profile)
        self.assertTrue(isinstance(entity, base.Profile))
        self.assertEqual(entity.handle, profile.handle)
        self.assertEqual(entity.raw_content, "")
        self.assertEqual(entity.public, False)
        self.assertEqual(entity.guid, profile.guid)
        self.assertEqual(entity.name, profile.name)
        self.assertEqual(entity.public_key, profile.rsa_public_key)
        self.assertEqual(entity.image_urls, {
            "small": profile.safer_image_url_small,
            "medium": profile.safer_image_url_medium,
            "large": profile.safer_image_url_large,
        })
        profile = ProfileFactory(visibility=Visibility.LIMITED)
        entity = make_federable_profile(profile)
        self.assertEqual(entity.public, False)
        profile = ProfileFactory(visibility=Visibility.SITE)
        entity = make_federable_profile(profile)
        self.assertEqual(entity.public, False)
        profile = ProfileFactory(visibility=Visibility.PUBLIC)
        entity = make_federable_profile(profile)
        self.assertEqual(entity.public, True)


class TestSenderKeyFetcher(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()

    def test_existing_remote_profile_public_key_is_returned(self):
        self.assertEqual(sender_key_fetcher(self.remote_profile.handle), self.remote_profile.rsa_public_key)

    def test_local_profile_is_skipped(self):
        self.assertIsNone(sender_key_fetcher(self.profile.handle), self.profile.rsa_public_key)

    @patch("socialhome.federate.utils.tasks.retrieve_remote_profile")
    @patch("socialhome.federate.utils.tasks.Profile.from_remote_profile")
    def test_remote_profile_public_key_is_returned(self, mock_from_remote, mock_retrieve):
        remote_profile = Mock(rsa_public_key="foo")
        mock_retrieve.return_value = mock_from_remote.return_value = remote_profile
        self.assertEqual(sender_key_fetcher("bar"), "foo")
        mock_retrieve.assert_called_once_with("bar")
        mock_from_remote.assert_called_once_with(remote_profile)

    @patch("socialhome.federate.utils.tasks.retrieve_remote_profile", return_value=None)
    @patch("socialhome.federate.utils.tasks.logger.warning")
    def test_nonexisting_remote_profile_is_logged(self, mock_logger, mock_retrieve):
        self.assertEqual(sender_key_fetcher("bar"), None)
        mock_logger.assert_called_once_with("get_sender_profile - Remote profile %s not found locally "
                                            "or remotely.", "bar")
