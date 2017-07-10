from socialhome.users.models import Profile
from socialhome.users.tables import FollowedTable


class ProfileSearchTable(FollowedTable):
    """Use our existing profile list table."""

    class Meta:
        model = Profile
        fields = ()
        order_by = ("name", "handle")
        template = "django_tables2/bootstrap.html"
        sequence = ("picture", "name", "handle")
