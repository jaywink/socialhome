# Generated by Django 3.2.18 on 2025-01-09 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0042_fill_content_has_had_local_replies'),
    ]

    operations = [
        migrations.AlterField(
            model_name='content',
            name='through',
            field=models.PositiveIntegerField(db_index=True, default=0, editable=False, verbose_name='Latest share id'),
        ),
    ]
