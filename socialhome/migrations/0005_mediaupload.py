# Generated by Django 3.2.18 on 2024-09-25 17:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('socialhome', '0004_add_default_policy_docs'),
    ]

    operations = [
        migrations.CreateModel(
            name='MediaUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('media', models.FileField(blank=True, null=True, upload_to='uploads/%Y/%m/%d/')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mediauploads', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
