from django.db import migrations
from django.db.migrations import RunPython

from socialhome.content.enums import ContentType


def forward(apps, schema_editor):
    Content = apps.get_model("content", "Content")
    # Just fill the new field with the assumption that root content may have had local replies.
    # This matches the old behaviour and updating every single content item in a large database
    # would probably not be worth it.
    Content.objects.filter(content_type=ContentType.CONTENT).update(has_had_local_replies=True)


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0041_content_has_had_local_replies'),
    ]

    operations = [
        RunPython(forward, RunPython.noop),
    ]
