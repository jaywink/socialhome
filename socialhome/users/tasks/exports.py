import datetime
import json
import os
import zipfile

import django_rq
from django.conf import settings
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.timezone import now

from socialhome.content.models import Content
from socialhome.content.serializers import ContentSerializer
from socialhome.notifications.tasks import send_data_export_ready_notification
from socialhome.users.models import User
from socialhome.users.serializers import ProfileSerializer, UserSerializer, LimitedProfileSerializer


def create_user_export(user_id):
    user = User.objects.get(id=user_id)
    exporter = UserExporter(user=user)
    exporter.create()


class UserExporter:
    def __init__(self, user, request=None):
        self.user = user
        if request:
            self.request = request
        else:
            self.request = RequestFactory().get('/')
            self.request.user = self.user
        self.context = {
            'request': self.request,
        }
        self.data = {}
        self.data_json_path = os.path.join(self.path, 'data.json')
        self.images_zip_path = os.path.join(self.path, 'images.zip')
        self.name = '%s-%s.zip' % (settings.SOCIALHOME_DOMAIN, now().date().isoformat())

    def _create_final_zip(self):
        # Zip all together
        with zipfile.ZipFile(os.path.join(self.path, self.name), 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(self.data_json_path, arcname='data.json')
            zipf.write(self.images_zip_path, arcname='images.zip')
        # Remove the tmp files
        os.unlink(self.data_json_path)
        os.unlink(self.images_zip_path)

    def _remove_previous_export(self):
        # Remove old ones first
        files = os.listdir(self.path)
        for file in files:
            os.unlink(os.path.join(self.path, file))

    def _store_data(self):
        # Data
        export = json.dumps(self.data, indent=2)
        with open(self.data_json_path, 'w') as exportf:
            exportf.writelines(export)

    def _store_images(self):
        # Images
        with zipfile.ZipFile(self.images_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for image in self.user.imageuploads.all():
                zipf.write(image.image.path, arcname=image.image.name)

    def collect_data(self):
        # User
        serializer = UserSerializer(instance=self.user, context=self.context)
        self.data['user'] = serializer.data
        # Profile
        serializer = ProfileSerializer(instance=self.user.profile, context=self.context)
        self.data['profile'] = serializer.data
        # Followed profiles
        self.data['following'] = []
        for follow in self.user.profile.following.all():
            serializer = LimitedProfileSerializer(instance=follow, context=self.context)
            self.data['following'].append(serializer.data)
        # Content
        self.data['content'] = []
        content_qs = Content.objects.filter(author=self.user.profile).order_by('created')
        for content in content_qs:
            serializer = ContentSerializer(instance=content, context=self.context)
            self.data['content'].append(serializer.data)

    def create(self):
        self.collect_data()
        self.store()
        self.notify()

    @property
    def file_date(self):
        if self.file_path:
            stat = os.stat(self.file_path)
            return datetime.datetime.fromtimestamp(stat.st_ctime, tz=timezone.get_current_timezone())

    @cached_property
    def file_path(self):
        files = os.listdir(self.path)
        if not files:
            return
        file = files[0]
        return os.path.join(self.path, file)

    @cached_property
    def path(self):
        path = os.path.join(settings.SOCIALHOME_EXPORTS_PATH, str(self.user.id))
        if not os.path.isdir(path):
            os.makedirs(path)
        return path

    def notify(self):
        django_rq.enqueue(send_data_export_ready_notification, self.user.id)

    def retrieve(self):
        if self.file_path:
            return open(self.file_path, 'rb')

    def store(self):
        self._remove_previous_export()
        self._store_data()
        self._store_images()
        self._create_final_zip()
