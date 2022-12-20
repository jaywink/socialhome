from unittest import mock
from unittest.mock import patch, Mock, call

import django_rq

from federation.entities.activitypub.enums import ActivityType

from socialhome.content.enums import ContentType
from socialhome.content.models import Tag
from socialhome.content.tests.factories import ContentFactory
from socialhome.enums import Visibility
from socialhome.federate.tasks import send_content, send_reply, send_share
from socialhome.notifications.tasks import send_reply_notifications, send_share_notification, send_mention_notification
from socialhome.streams.streams import update_streams_with_content
from socialhome.tests.utils import SocialhomeTestCase, SocialhomeTransactionTestCase
from socialhome.users.tests.factories import UserFactory, PublicUserFactory, ProfileFactory


class TestContentMentionsChange(SocialhomeTransactionTestCase):
    def setUp(self):
        super().setUp()
        self.content = ContentFactory()
        self.user = UserFactory()
        self.profile = self.user.profile

    @patch("socialhome.content.signals.django_rq.queues.DjangoRQ", autospec=True)
    def test_adding_mention_triggers_notification(self, mock_queue):
        self.content.mentions.add(self.profile)
        self.assertEqual(mock_queue.method_calls,
            [call().enqueue(send_mention_notification, self.user.id, self.content.author.id, self.content.id)]
        )

    @patch("socialhome.content.signals.django_rq.queues.DjangoRQ", autospec=True)
    def test_adding_mention_triggers_notification__only_once(self, mock_queue):
        self.content.mentions.add(self.profile)
        self.content.mentions.add(self.profile)
        self.content.mentions.add(self.profile)
        self.content.mentions.add(self.profile)
        self.assertEqual(mock_queue.method_calls,
            [call().enqueue(send_mention_notification, self.user.id, self.content.author.id, self.content.id)]
        )

    @patch("socialhome.content.signals.django_rq.queues.DjangoRQ", autospec=True)
    def test_removing_mention_does_not_trigger_notification(self, mock_queue):
        self.content.mentions.add(self.profile)
        mock_queue.reset_mock()
        self.content.mentions.remove(self.profile)
        assert len(mock_queue.method_calls) == 0


class TestContentPostSave(SocialhomeTransactionTestCase):
    @patch("socialhome.content.signals.update_streams_with_content")
    def test_calls_update_streams_with_content(self, mock_update):
        # Calls on create
        content = ContentFactory()
        mock_update.assert_called_once_with(content, event='new')
        mock_update.reset_mock()
        # Call on update (TODO: implement stream updates)
        content.text = "update!"
        content.save()
        mock_update.assert_called_once_with(content, event='update')


class TestNotifyListeners(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.create_local_and_remote_user()

    @patch("socialhome.streams.consumers.async_to_sync", autospec=True)
    def test_content_save_calls_streamconsumer_group_send__public_no_tags_no_followers(self, mock_async):
        mock_send = Mock()
        mock_async.return_value = mock_send
        content = ContentFactory()
        with patch("socialhome.users.models.User.recently_active", new_callable=mock.PropertyMock, return_value=True):
            update_streams_with_content(content)
        data = {"type": "notification", "payload": {"event": "new", "id": content.id, "parentId": None}}
        calls = [
            call(f"streams_profile_all__{content.author.id}__{self.user.id}", data),
            call(f"streams_public__{self.user.id}", data),
        ]
        mock_send.assert_has_calls(calls, any_order=True)
        self.assertEqual(mock_send.call_count, 2)

    @patch("socialhome.streams.consumers.async_to_sync", autospec=True)
    def test_content_save_calls_streamconsumer_group_send__user_not_recently_active(self, mock_async):
        mock_send = Mock()
        mock_async.return_value = mock_send
        content = ContentFactory()
        update_streams_with_content(content)
        mock_send.assert_not_called()

    @patch("socialhome.streams.consumers.async_to_sync", autospec=True)
    def test_content_save_calls_streamconsumer_group_send__limited_tags_and_followers(self, mock_async):
        mock_send = Mock()
        mock_async.return_value = mock_send
        PublicUserFactory()
        self.profile.following.add(self.remote_profile)
        content = ContentFactory(author=self.remote_profile, visibility=Visibility.LIMITED, text="#foobar #barfoo")
        content.limited_visibilities.add(self.profile)
        with patch("socialhome.users.models.User.recently_active", new_callable=mock.PropertyMock, return_value=True):
            update_streams_with_content(content)
        data = {"type": "notification", "payload": {"event": "new", "id": content.id, "parentId": None}}
        foobar_id = Tag.objects.get(name="foobar").id
        barfoo_id = Tag.objects.get(name="barfoo").id
        calls = [
            call(f"streams_tag__{foobar_id}__{self.user.id}", data),
            call(f"streams_tag__{barfoo_id}__{self.user.id}", data),
            call(f"streams_profile_all__{content.author.id}__{self.user.id}", data),
            call(f"streams_followed__{self.user.id}", data),
            call(f"streams_limited__{self.user.id}", data),
        ]
        mock_send.assert_has_calls(calls, any_order=True)
        self.assertEqual(mock_send.call_count, 5)

    @patch("socialhome.streams.consumers.async_to_sync", autospec=True)
    def test_content_save_calls_streamconsumer_group_send__limited_no_followers(self, mock_async):
        mock_send = Mock()
        mock_async.return_value = mock_send
        content = ContentFactory(visibility=Visibility.LIMITED, text="#foobar #barfoo")
        update_streams_with_content(content)
        mock_send.assert_not_called()

    @patch("socialhome.streams.consumers.async_to_sync", autospec=True)
    def test_content_save_calls_streamconsumer_group_send__public_with_followers(self, mock_async):
        mock_send = Mock()
        mock_async.return_value = mock_send
        self.profile.following.add(self.remote_profile)
        other_user = PublicUserFactory()
        third_user = PublicUserFactory()
        other_user.profile.following.add(self.remote_profile)
        content = ContentFactory(author=self.remote_profile, text="#foobar #barfoo")
        with patch("socialhome.users.models.User.recently_active", new_callable=mock.PropertyMock, return_value=True):
            update_streams_with_content(content)
        data = {"type": "notification", "payload": {"event": "new", "id": content.id, 'parentId': None}}
        foobar_id = Tag.objects.get(name="foobar").id
        barfoo_id = Tag.objects.get(name="barfoo").id
        calls = [
            call(f"streams_tag__{foobar_id}__{self.user.id}", data),
            call(f"streams_tag__{foobar_id}__{other_user.id}", data),
            call(f"streams_tag__{foobar_id}__{third_user.id}", data),
            call(f"streams_tag__{barfoo_id}__{self.user.id}", data),
            call(f"streams_tag__{barfoo_id}__{other_user.id}", data),
            call(f"streams_tag__{barfoo_id}__{third_user.id}", data),
            call(f"streams_profile_all__{content.author.id}__{self.user.id}", data),
            call(f"streams_profile_all__{content.author.id}__{other_user.id}", data),
            call(f"streams_profile_all__{content.author.id}__{third_user.id}", data),
            call(f"streams_public__{self.user.id}", data),
            call(f"streams_public__{other_user.id}", data),
            call(f"streams_public__{third_user.id}", data),
            call(f"streams_followed__{self.user.id}", data),
            call(f"streams_followed__{other_user.id}", data),
        ]
        print(mock_send.mock_calls)
        mock_send.assert_has_calls(calls, any_order=True)
        self.assertEqual(mock_send.call_count, 14)

    @patch("socialhome.streams.consumers.async_to_sync", autospec=True)
    def test_content_save_calls_streamconsumer_group_send__public_share_with_followers(self, mock_async):
        mock_send = Mock()
        mock_async.return_value = mock_send
        self.profile.following.add(self.remote_profile)
        other_user = PublicUserFactory()
        other_profile = ProfileFactory()
        content = ContentFactory(author=self.remote_profile)
        share = ContentFactory(content_type=ContentType.SHARE, share_of=content, author=other_profile)
        with patch("socialhome.users.models.User.recently_active", new_callable=mock.PropertyMock, return_value=True):
            update_streams_with_content(share)
        data = {"type": "notification", "payload": {"event": "new", "id": content.id, "parentId": None}}
        calls = [
            call(f"streams_profile_all__{share.author.id}__{self.user.id}", data),
            call(f"streams_profile_all__{share.author.id}__{other_user.id}", data),
            call(f"streams_followed__{self.user.id}", data),
        ]
        mock_send.assert_has_calls(calls, any_order=True)
        self.assertEqual(mock_send.call_count, 3)

    @patch("socialhome.streams.consumers.async_to_sync", autospec=True)
    def test_content_save_calls_streamconsumer_group_send__replies(self, mock_async):
        mock_send = Mock()
        mock_async.return_value = mock_send
        content = ContentFactory()
        reply = ContentFactory(parent=content)
        with patch("socialhome.users.models.User.recently_active", new_callable=mock.PropertyMock, return_value=True):
            update_streams_with_content(reply)
        data = {"type": "notification", "payload": {"event": "new", "id": reply.id, "parentId": content.id}}
        calls = [
            call(f'streams_public__{self.user.id}', data),
            call(f'streams_profile_all__{content.author.id}__{self.user.id}', data),
            call(f'streams_content__{content.channel_group_name}', data),
        ]
        mock_send.assert_has_calls(calls, any_order=True)
        self.assertEqual(mock_send.call_count, 3)


class TestFederateContent(SocialhomeTransactionTestCase):
    @patch("socialhome.content.signals.django_rq.queues.DjangoRQ", autospec=True)
    @patch("socialhome.content.signals.update_streams_with_content", autospec=True)
    def test_non_local_content_does_not_get_sent(self, mock_update, mock_send):
        ContentFactory()
        assert len(mock_send.method_calls) == 0

    @patch("socialhome.content.signals.django_rq.queues.DjangoRQ", autospec=True)
    @patch("socialhome.content.signals.update_streams_with_content", autospec=True)
    def test_local_content_with_federate_false_does_not_get_sent(self, mock_update, mock_send):
        user = UserFactory()
        mock_send.reset_mock()
        ContentFactory(author=user.profile, federate=False)
        assert len(mock_send.method_calls) == 0

    @patch("socialhome.content.signals.django_rq.queues.DjangoRQ", autospec=True)
    def test_local_content_with_parent_sent_as_reply(self, mock_send):
        user = UserFactory()
        parent = ContentFactory(author=user.profile)
        mock_send.reset_mock()
        content = ContentFactory(author=user.profile, parent=parent)
        self.assertTrue(content.local)
        activity = content.activities.first()
        send_reply_notifications_found = send_reply_found = False
        for name, args, kwargs in mock_send.method_calls:
            if args == (send_reply_notifications, content.id):
                send_reply_notifications_found = True
            elif args[0] == send_reply and args[1] == content.id and args[2] == activity.fid:
                send_reply_found = True
        if not all([send_reply_notifications_found, send_reply_found]):
            self.fail()
        self.assertEqual(activity.type, ActivityType.CREATE)

    @patch("socialhome.content.signals.django_rq.queues.DjangoRQ", autospec=True)
    @patch("socialhome.content.signals.update_streams_with_content", autospec=True)
    def test_local_content_gets_sent(self, mock_update, mock_send):
        user = UserFactory()
        mock_send.reset_mock()
        content = ContentFactory(author=user.profile)
        self.assertTrue(content.local)
        assert len(mock_send.method_calls) == 1
        name, args, kwargs = mock_send.method_calls[0]
        self.assertEqual(name, '().enqueue')
        self.assertEqual(args[0], send_content)
        self.assertEqual(args[1], content.id)
        self.assertEqual(kwargs, {'recipient_id': None})
        activity = content.activities.first()
        self.assertEqual(args[2], activity.fid)
        self.assertEqual(activity.type, ActivityType.CREATE)

    @patch("socialhome.content.signals.django_rq.queues.DjangoRQ", autospec=True)
    @patch("socialhome.content.signals.update_streams_with_content", autospec=True)
    def test_local_content_update_gets_sent(self, mock_update, mock_send):
        user = UserFactory()
        content = ContentFactory(author=user.profile)
        self.assertTrue(content.local)
        mock_send.reset_mock()
        content.text = "foobar edit"
        content.save()
        assert len(mock_send.method_calls) == 1
        name, args, kwargs = mock_send.method_calls[0]
        self.assertEqual(name, '().enqueue')
        self.assertEqual(args[0], send_content)
        self.assertEqual(args[1], content.id)
        self.assertEqual(kwargs, {'recipient_id': None})
        activity = content.activities.order_by('-created').first()
        self.assertEqual(args[2], activity.fid)
        self.assertEqual(activity.type, ActivityType.UPDATE)

    @patch("socialhome.content.signals.django_rq.queues.DjangoRQ", autospec=True)
    @patch("socialhome.content.signals.update_streams_with_content")
    def test_share_gets_sent(self, mock_update, mock_send):
        user = UserFactory()
        user2 = UserFactory()
        share_of = ContentFactory(author=user2.profile)
        mock_send.reset_mock()
        content = ContentFactory(author=user.profile, share_of=share_of)
        name, args, kwargs = mock_send.method_calls[0]
        self.assertEqual(name, '().enqueue')
        self.assertEqual(args, (send_share_notification, content.id))
        name, args, kwargs = mock_send.method_calls[1]
        self.assertEqual(name, '().enqueue')
        self.assertEqual(args[0], send_share)
        self.assertEqual(args[1], content.id)
        activity = content.activities.first()
        self.assertEqual(args[2], activity.fid)
        self.assertEqual(activity.type, ActivityType.CREATE)


class TestFederateContentRetraction(SocialhomeTestCase):
    @patch("socialhome.content.signals.django_rq.queues.DjangoRQ", autospec=True)
    def test_non_local_content_retraction_does_not_get_sent(self, mock_send):
        content = ContentFactory()
        content.delete()
        self.assertTrue(mock_send.enqueue.called is False)

    @patch("socialhome.content.signals.send_content_retraction", autospec=True)
    def test_local_content_retraction_gets_sent(self, mock_send):
        user = UserFactory()
        content = ContentFactory(author=user.profile)
        self.assertTrue(content.local)
        mock_send.reset_mock()
        content.delete()
        mock_send.assert_called_once_with(content, content.author_id)

    @patch("socialhome.content.signals.send_content_retraction", autospec=True, side_effect=Exception)
    @patch("socialhome.content.signals.logger.exception")
    def test_exception_calls_logger(self, mock_logger, mock_send):
        user = UserFactory()
        content = ContentFactory(author=user.profile)
        content.delete()
        self.assertTrue(mock_logger.called)


class TestFetchPreview(SocialhomeTestCase):
    @patch("socialhome.content.signals.fetch_content_preview", autospec=True)
    def test_fetch_content_preview_called(self, fetch):
        ContentFactory()
        self.assertEqual(fetch.call_count, 1)

    @patch("socialhome.content.signals.fetch_content_preview", side_effect=Exception)
    @patch("socialhome.content.signals.logger.exception")
    def test_fetch_content_preview_exception_logger_called(self, logger, fetch):
        ContentFactory()
        self.assertTrue(logger.called)


class TestRenderContent(SocialhomeTestCase):
    def test_render_content_called(self):
        content = ContentFactory()
        content.render = Mock()
        content.save()
        content.render.assert_called_once_with()

    @patch("socialhome.content.signals.logger.exception")
    def test_render_content_exception_logger_called(self, logger):
        content = ContentFactory()
        content.render = Mock(side_effect=Exception)
        content.save()
        self.assertTrue(logger.called)
