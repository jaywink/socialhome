import dramatiq
from django.conf import settings


@dramatiq.actor(priority=settings.DRAMATIQ_PRIORITY_LOW)
def update_profile_from_fed(profile_id):
    """
    FIXME: Once RQ is removed, move the called function code here.
    It needs to live where it is until RQ queues are processed.
    """
    from socialhome.users import utils
    utils.update_profile_from_fed(profile_id)
