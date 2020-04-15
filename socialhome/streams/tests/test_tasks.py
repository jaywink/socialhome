from datetime import timedelta
from unittest.mock import Mock

from django.test.utils import override_settings
from django.utils.timezone import now

from socialhome.streams.tasks import streams_tasks, groom_redis_precaches, delete_redis_keys
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.models import User
from socialhome.users.tests.factories import UserFactory
from socialhome.utils import get_redis_connection


def test_streams_tasks():
    mock_scheduler = Mock()
    streams_tasks(mock_scheduler)
    _args, kwargs = mock_scheduler.schedule.call_args_list[0]
    assert kwargs["func"] == delete_redis_keys
    _args, kwargs = mock_scheduler.schedule.call_args_list[1]
    assert kwargs["func"] == groom_redis_precaches


@override_settings(
    SOCIALHOME_STREAMS_PRECACHE_SIZE=4, SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE=2,
    SOCIALHOME_STREAMS_PRECACHE_INACTIVE_DAYS=10,
)
class TestGroomRedisPrecaches(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()

    def setUp(self):
        super().setUp()
        self.r = get_redis_connection()
        for x in range(10):
            self.r.zadd("sh:streams:spamandeggs:736353:%s" % self.user.id, {str(x**x): x})
        for x in range(10):
            self.r.hset("sh:streams:spamandeggs:736353:%s:throughs" % self.user.id, str(x**x), x**x+1)

    def test_grooming_should_keep_top_x__active_user(self):
        expected_z = {x: str(x ** x) for x in range(6, 10)}
        expected_h = {str(x ** x): str(x ** x + 1) for x in range(6, 10)}
        User.objects.filter(id=self.user.id).update(
            last_login=now() - timedelta(days=9),
        )
        groom_redis_precaches()
        zitems = self.r.zrange("sh:streams:spamandeggs:736353:%s" % self.user.id, 0, 10, withscores=True)
        zitems = {int(score): value.decode("utf-8") for value, score in zitems}
        self.assertEqual(zitems, expected_z)
        hitems = self.r.hgetall("sh:streams:spamandeggs:736353:%s:throughs" % self.user.id)
        hitems = {key.decode("utf-8"): value.decode("utf-8") for key, value in hitems.items()}
        self.assertEqual(hitems, expected_h)

    def test_grooming_should_keep_top_x__inactive_user(self):
        expected_z = {x: str(x ** x) for x in range(8, 10)}
        expected_h = {str(x ** x): str(x ** x + 1) for x in range(8, 10)}
        User.objects.filter(id=self.user.id).update(
            last_login=now() - timedelta(days=11),
        )
        groom_redis_precaches()
        zitems = self.r.zrange("sh:streams:spamandeggs:736353:%s" % self.user.id, 0, 10, withscores=True)
        zitems = {int(score): value.decode("utf-8") for value, score in zitems}
        self.assertEqual(zitems, expected_z)
        hitems = self.r.hgetall("sh:streams:spamandeggs:736353:%s:throughs" % self.user.id)
        hitems = {key.decode("utf-8"): value.decode("utf-8") for key, value in hitems.items()}
        self.assertEqual(hitems, expected_h)

    @override_settings(SOCIALHOME_STREAMS_PRECACHE_SIZE=0, SOCIALHOME_STREAMS_PRECACHE_INACTIVE_DAYS=10)
    def test_grooming_should_allow_defining_none__active_user(self):
        User.objects.filter(id=self.user.id).update(
            last_login=now() - timedelta(days=9),
        )
        groom_redis_precaches()
        self.assertFalse(self.r.exists("sh:streams:spamandeggs:736353:%s" % self.user.id))
        self.assertFalse(self.r.exists("sh:streams:spamandeggs:736353:%s:throughs" % self.user.id))

    @override_settings(SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE=0, SOCIALHOME_STREAMS_PRECACHE_INACTIVE_DAYS=10)
    def test_grooming_should_allow_defining_none__inactive_user(self):
        User.objects.filter(id=self.user.id).update(
            last_login=now() - timedelta(days=11),
        )
        groom_redis_precaches()
        self.assertFalse(self.r.exists("sh:streams:spamandeggs:736353:%s" % self.user.id))
        self.assertFalse(self.r.exists("sh:streams:spamandeggs:736353:%s:throughs" % self.user.id))

    def test_user_fetched_from_db_only_once(self):
        User.objects.filter(id=self.user.id).update(
            last_login=now() - timedelta(days=9),
        )
        with self.assertNumQueries(1):
            groom_redis_precaches()
        User.objects.filter(id=self.user.id).update(
            last_login=now() - timedelta(days=11),
        )
        with self.assertNumQueries(1):
            groom_redis_precaches()
