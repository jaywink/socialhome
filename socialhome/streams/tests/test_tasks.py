from datetime import datetime
from unittest.mock import Mock

from django.test.utils import override_settings
from freezegun import freeze_time

from socialhome.streams.tasks import streams_tasks, groom_redis_precaches
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.utils import get_redis_connection


@freeze_time("2016-04-02")
def test_streams_tasks():
    mock_scheduler = Mock()
    streams_tasks(mock_scheduler)
    mock_scheduler.schedule.assert_called_once_with(
        scheduled_time=datetime.utcnow(),
        func=groom_redis_precaches,
        interval=60 * 60 * 24,
    )


@override_settings(SOCIALHOME_STREAMS_PRECACHE_SIZE=4)
class TestGroomRedisPrecaches(SocialhomeTestCase):
    def setUp(self):
        super().setUp()
        self.r = get_redis_connection()
        for x in range(10):
            self.r.zadd("sh:streams:spamandeggs:1", x, str(x**x))
        self.expected_z = {x: str(x**x) for x in range(7, 10)}
        for x in range(10):
            self.r.hset("sh:streams:spamandeggs:1:throughs", str(x**x), x**x+1)
        self.expected_h = {str(x**x): str(x**x+1) for x in range(7, 10)}

    def test_grooming_should_keep_top_x(self):
        groom_redis_precaches()
        zitems = self.r.zrange("sh:streams:spamandeggs:1", 0, 10, withscores=True)
        zitems = {int(score): value.decode("utf-8") for value, score in zitems}
        self.assertEqual(zitems, self.expected_z)
        hitems = self.r.hgetall("sh:streams:spamandeggs:1:throughs")
        hitems = {key.decode("utf-8"): value.decode("utf-8") for key, value in hitems.items()}
        self.assertEqual(hitems, self.expected_h)
