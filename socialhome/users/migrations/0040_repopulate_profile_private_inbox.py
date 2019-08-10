from django.db import migrations
from django.db.migrations import RunPython


def forward(apps, schema_editor):
    # noinspection PyPep8Naming
    Profile = apps.get_model("users", "Profile")
    for profile in Profile.objects.filter(user__isnull=False).select_related('user').iterator():
        inbox = f"{profile.fid}inbox/"
        Profile.objects.filter(id=profile.id).update(inbox_private=inbox)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0039_repopulate_profile_fid'),
    ]

    operations = [
        RunPython(forward, RunPython.noop)
    ]
