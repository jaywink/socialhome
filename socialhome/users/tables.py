import django_tables2

from socialhome.users.models import Profile


class FollowedTable(django_tables2.Table):
    class Meta:
        model = Profile
        fields = ("name", "handle")
