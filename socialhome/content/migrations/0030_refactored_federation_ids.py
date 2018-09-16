# Generated by Django 2.0.8 on 2018-09-16 17:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0029_remove_content_mention_recipients'),
    ]

    operations = [
        migrations.AddField(
            model_name='content',
            name='fid',
            field=models.URLField(blank=True, editable=False, max_length=255, null=True, unique=True, verbose_name='Federation ID'),
        ),
        migrations.AddField(
            model_name='content',
            name='uuid',
            field=models.UUIDField(unique=True, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='content',
            name='guid',
            field=models.CharField(blank=True, editable=False, max_length=255, null=True, unique=True, verbose_name='GUID'),
        ),
    ]
