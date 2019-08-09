from django.conf import settings
from django.db import migrations
from django.db.migrations import RunPython
from django.urls import reverse


def forward(apps, schema_editor):
    """
    YES THIS IS DESTRUCTIVE IF YOU'VE BEEN RUNNING ON DEVELOPMENT BRANCH WITH ALPHA ACTIVITYPUB ENABLED!!!!

    If you have, re-create all your relations to other servers via ActivityPub.
    """
    # noinspection PyPep8Naming
    Profile = apps.get_model("users", "Profile")
    for profile in Profile.objects.filter(user__isnull=False).select_related('user').iterator():
        url = reverse("users:detail", kwargs={"username": profile.user.username})
        fid = f"{settings.SOCIALHOME_URL}{url}"
        Profile.objects.filter(id=profile.id).update(fid=fid)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0038_populate_profile_protocol'),
    ]

    operations = [
        RunPython(forward, RunPython.noop)
    ]
