from unittest.mock import Mock

import pytest
from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers

from socialhome.content.models import Content
from socialhome.content.serializers import ContentSerializer
from socialhome.content.tests.factories import PublicContentFactory, TagFactory, LimitedContentFactory, \
    LimitedContentWithRecipientsFactory
from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import PublicProfileFactory, PublicUserFactory, UserWithContactFactory


class ContentSerializerTestCase(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.create_local_and_remote_user()
        cls.user_recipient = PublicProfileFactory()
        cls.user_recipient2 = PublicProfileFactory()
        cls.content = PublicContentFactory(author=cls.remote_profile)
        cls.content2 = PublicContentFactory(author=cls.remote_profile)
        cls.limited_content = LimitedContentFactory(author=cls.remote_profile)
        cls.limited_content2 = LimitedContentFactory(author=cls.profile)
        cls.limited_content_with_recipients = LimitedContentWithRecipientsFactory(recipients=[
            cls.user_recipient, cls.user_recipient2
        ])
        cls.user_content = PublicContentFactory(author=cls.profile)
        cls.share = PublicContentFactory(share_of=cls.content)
        cls.reply = PublicContentFactory(parent=cls.content)
        cls.reply_parent_with_recipients = PublicContentFactory(parent=cls.limited_content_with_recipients)

    def setUp(self):
        super().setUp()
        try:
            del self.profile.following_ids
        except AttributeError:
            pass

    def test_create_with_parent(self):
        serializer = ContentSerializer(context={"request": Mock(user=self.user)}, data={
            "text": "With parent", "visibility": "public", "parent": self.content.id,
        })
        self.assertTrue(serializer.is_valid())
        serializer.save(author=self.user.profile)
        content = Content.objects.order_by("id").last()
        self.assertEqual(content.text, "With parent")
        self.assertEqual(content.parent, self.content)
        self.assertEqual(content.root_parent, self.content)

    def test_create_with_parent__user_cannot_see_parent(self):
        serializer = ContentSerializer(context={"request": Mock(user=self.user)}, data={
            "text": "With parent cannot seeee it", "visibility": "limited", "parent": self.limited_content.id,
        })
        self.assertFalse(serializer.is_valid())

    def test_create_with_parent__visibility_does_not_match_parent(self):
        serializer = ContentSerializer(context={"request": Mock(user=self.user)}, data={
            "text": "With parent visibility mismatch", "visibility": "public", "parent": self.limited_content.id,
        })
        self.assertFalse(serializer.is_valid())

    def test_create_with_visibility(self):
        serializer = ContentSerializer(context={"request": Mock(user=self.user)}, data={
            "text": "With visibility", "visibility": "public",
        })
        self.assertTrue(serializer.is_valid())
        serializer.save(author=self.user.profile)
        content = Content.objects.order_by("id").last()
        self.assertEqual(content.text, "With visibility")
        self.assertEqual(content.visibility, Visibility.PUBLIC)

    def test_create_without_parent(self):
        serializer = ContentSerializer(context={"request": Mock(user=self.user)}, data={
            "text": "Without parent", "visibility": "public",
        })
        self.assertTrue(serializer.is_valid())
        serializer.save(author=self.user.profile)
        content = Content.objects.order_by("id").last()
        self.assertEqual(content.text, "Without parent")

    def test_create_without_visibility(self):
        serializer = ContentSerializer(context={"request": Mock(user=self.user)}, data={
            "text": "Without visibility",
        })
        self.assertFalse(serializer.is_valid())

    def test_create_without_visibility__reply(self):
        serializer = ContentSerializer(context={"request": Mock(user=self.user)}, data={
            "text": "Without visibility", "parent": self.limited_content2.id,
        })
        self.assertTrue(serializer.is_valid())
        serializer.save(author=self.profile)
        content = Content.objects.order_by("id").last()
        self.assertEqual(content.text, "Without visibility")
        # Inherits from parent
        self.assertEqual(content.visibility, Visibility.LIMITED)
        self.assertEqual(content.parent, self.limited_content2)
        self.assertEqual(content.root_parent, self.limited_content2)

    def test_has_twitter_oembed(self):
        serializer = ContentSerializer(self.content)
        self.assertFalse(serializer.data["has_twitter_oembed"])

    def test_serializes_author(self):
        serializer = ContentSerializer(self.content)
        data = serializer.data["author"]
        self.assertEqual(data["uuid"], str(self.remote_profile.uuid))
        self.assertEqual(data["handle"], self.remote_profile.handle)
        self.assertEqual(data["home_url"], self.remote_profile.home_url)
        self.assertEqual(data["id"], self.remote_profile.id)
        self.assertEqual(data["fid"], self.remote_profile.fid)
        self.assertEqual(data["image_url_small"], self.remote_profile.image_url_small)
        self.assertEqual(data["is_local"], self.remote_profile.is_local)
        self.assertEqual(data["name"], self.remote_profile.name)
        self.assertEqual(data["url"], self.remote_profile.url)

    def test_save__collects_recipients(self):
        serializer = ContentSerializer(
            instance=self.limited_content, partial=True, context={"request": Mock(user=self.user)}, data={
                "recipients": [self.user_recipient.handle, self.user_recipient2.handle],
                "visibility": Visibility.LIMITED.value
            },
        )
        serializer.is_valid()
        content = serializer.save()

        self.assertEqual(set(content.limited_visibilities.all()), {self.user_recipient, self.user_recipient2})

    def test_save__collects_recipients__reply_copies_from_parent(self):
        serializer = ContentSerializer(
            instance=self.reply_parent_with_recipients,
            partial=True,
            context={"request": Mock(user=self.user)},
            data={
                "recipients": [self.user_recipient.handle, self.user_recipient2.handle],
                "visibility": Visibility.LIMITED.value
            },
        )

        serializer.is_valid(raise_exception=True)
        content = serializer.save()

        actual = set(content.limited_visibilities.all().order_by("id"))
        self.assertSetEqual({self.user_recipient, self.user_recipient2}, actual)

    def test_save__removes_removed_recipients(self):
        serializer = ContentSerializer(
            instance=self.limited_content_with_recipients,
            partial=True,
            context={"request": Mock(user=self.user)},
            data={
                "recipients": [self.user_recipient.handle, self.user_recipient2.handle],
                "visibility": Visibility.LIMITED.value,
            },
        )

        serializer.is_valid(raise_exception=True)
        content = serializer.save()

        actual = set(content.limited_visibilities.all().order_by("id"))
        self.assertSetEqual(actual, {self.user_recipient, self.user_recipient2})

        # Remove one recipient
        serializer = ContentSerializer(
            instance=content,
            partial=True,
            context={"request": Mock(user=self.user)},
            data={
                "recipients": [self.user_recipient.handle],
                "visibility": Visibility.LIMITED.value
            },
        )

        serializer.is_valid(raise_exception=True)
        content = serializer.save()
        self.assertSetEqual(set(content.limited_visibilities.all()), {self.user_recipient})

    def test_save__collects_recipients__include_following(self):
        user = UserWithContactFactory()
        content = LimitedContentFactory(author=user.profile)
        serializer = ContentSerializer(
            instance=content,
            partial=True,
            context={"request": Mock(user=user)},
            data={
                "recipients": [self.user_recipient.handle, self.user_recipient2.handle],
                "visibility": Visibility.LIMITED.value,
                "include_following": True,
            })
        serializer.is_valid(raise_exception=True)
        content = serializer.save()

        actual = set(content.limited_visibilities.all().order_by("id"))
        expected = set(
            list(user.profile.following.all().order_by("id")) +
            [self.user_recipient, self.user_recipient2]
        )
        self.assertSetEqual(actual, expected)

    def test_serializes_through(self):
        serializer = ContentSerializer(self.content)
        self.assertEqual(serializer.data["through"], self.content.id)
        serializer = ContentSerializer(self.content, context={"throughs": {self.content.id: 666}})
        self.assertEqual(serializer.data["through"], 666)

    def test_serializes_share_of(self):
        serializer = ContentSerializer(self.content)
        self.assertIsNone(serializer.data["share_of"])
        serializer = ContentSerializer(self.share)
        self.assertEqual(serializer.data["share_of"], self.content.id)

    def test_serialize__recipients_list_empty_for_not_owners(self):
        limited_content = LimitedContentWithRecipientsFactory(author=self.user.profile)
        serializer = ContentSerializer(limited_content, context={"request": Mock(user=self.user)})
        expected_recipients_list = set(
            limited_content.limited_visibilities.all().order_by("id").values_list("finger", flat=True)
        )
        self.assertEqual(expected_recipients_list, set(serializer.data["recipients"]))

        serializer = ContentSerializer(limited_content, context={"request": Mock(user=PublicUserFactory())})
        self.assertEqual(set(serializer.data["recipients"]), set())

    def test_user_is_author_false_if_no_request(self):
        serializer = ContentSerializer()
        self.assertFalse(serializer.get_user_is_author(None))

    def test_user_is_author_false_if_not_authenticated(self):
        serializer = ContentSerializer(context={"request": Mock(user=AnonymousUser())})
        self.assertFalse(serializer.get_user_is_author(None))

    def test_user_is_author_false_if_not_author(self):
        serializer = ContentSerializer(context={"request": Mock(user=self.user)})
        self.assertFalse(serializer.get_user_is_author(self.content))

    def test_user_is_author_true_if_author(self):
        serializer = ContentSerializer(context={"request": Mock(user=self.user)})
        self.assertTrue(serializer.get_user_is_author(self.user_content))

    def test_user_has_shared_false_if_no_request(self):
        serializer = ContentSerializer()
        self.assertFalse(serializer.get_user_has_shared(None))

    def test_user_has_shared_false_if_anonymous_user(self):
        serializer = ContentSerializer(context={"request": Mock(user=AnonymousUser())})
        self.assertFalse(serializer.get_user_has_shared(None))

    def test_user_has_shared_false_if_not_shared(self):
        serializer = ContentSerializer(context={"request": Mock(user=self.user)})
        self.assertFalse(serializer.get_user_has_shared(self.content))

    def test_user_has_shared_true_if_shared(self):
        self.content.share(self.profile)
        serializer = ContentSerializer(context={"request": Mock(user=self.user)})
        self.assertTrue(serializer.get_user_has_shared(self.content))

    def test_tags_if_no_tag(self):
        self.content.tags.clear()
        serializer = ContentSerializer(self.content, context={"request": Mock(user=self.user)})
        self.assertEqual(serializer.data["tags"], [])

    def test_tags_with_tag(self):
        tag = TagFactory(name="yolo")
        self.content.tags.clear()
        self.content.tags.add(tag)
        serializer = ContentSerializer(self.content, context={"request": Mock(user=self.user)})
        self.assertEqual(serializer.data["tags"], ["yolo"])

    def test_update_doesnt_allow_changing_parent(self):
        serializer = ContentSerializer(
            instance=self.reply, partial=True, context={"request": Mock(user=self.user)}, data={
                "parent": self.content.id,
            },
        )
        self.assertTrue(serializer.is_valid())
        serializer = ContentSerializer(
            instance=self.reply, partial=True, context={"request": Mock(user=self.user)}, data={
                "parent": self.content2.id,
            },
        )
        self.assertFalse(serializer.is_valid())

    def test_validate_recipients(self):
        serializer = ContentSerializer(
            instance=self.limited_content, partial=True, context={"request": Mock(user=self.user)}, data={
                "recipients": [self.user_recipient.handle, self.user_recipient2.handle],
                "visibility": Visibility.LIMITED.value
            },
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["recipients"],
                          {self.user_recipient.handle, self.user_recipient2.handle})

    def test_validate_recipients__fails_bad_recipients(self):
        serializer = ContentSerializer(
            instance=self.limited_content, partial=True, context={"request": Mock(user=self.user)}, data={
                "recipients": [f"{self.user_recipient.handle}+bad_ext", f"{self.user_recipient2.handle}+bad_ext"],
                "visibility": Visibility.LIMITED.value
            },
        )
        with pytest.raises(serializers.ValidationError, match=r".*Not all recipients could be found\..*"):
            serializer.is_valid(raise_exception=True)

    def test_validate_recipients__recipients_and_include_following_cant_both_be_empty(self):
        serializer = ContentSerializer(
            instance=self.limited_content, partial=True, context={"request": Mock(user=self.user)}, data={
                "recipients": "",
                "include_following": False,
                "visibility": Visibility.LIMITED.value
            },
        )
        with pytest.raises(
            serializers.ValidationError,
            match=r".*Recipients cannot be empty if not including followed users\..*"
        ):
            serializer.is_valid(raise_exception=True)

    # recipients == mentions, so not ignored anymore
    @pytest.mark.skip
    def test_validate_recipients__recipients_ignored_if_not_limited(self):
        serializer = ContentSerializer(
            instance=self.limited_content, partial=True, context={"request": Mock(user=self.user)}, data={
                "recipients": f"{self.user_recipient.handle},{self.user_recipient2.handle}",
                "visibility": Visibility.PUBLIC.value
            },
        )

        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.validated_data["recipients"], set())
