# Generated by Django 3.2.18 on 2023-11-26 14:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0039_auto_20221220_1457'),
    ]

    operations = [
        migrations.AddField(
            model_name='content',
            name='through',
            field=models.PositiveIntegerField(default=0, editable=False, verbose_name='Latest share id'),
        ),
    ]