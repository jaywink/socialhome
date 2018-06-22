from unittest.mock import Mock, patch

from django.contrib.admin import AdminSite

from socialhome.admin import PolicyDocumentAdmin
from socialhome.enums import PolicyDocumentType
from socialhome.models import PolicyDocument
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import AdminUserFactory


@patch('socialhome.admin.messages', new=Mock())
class TestPolicyDocumentAdmin(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.site = AdminSite()
        cls.user = AdminUserFactory()
        cls.request = cls.get_request(cls.user)
        if PolicyDocument.objects.count() == 0:
            # Pytest ignores data migrations for some reason..
            # Possibly related? https://github.com/pytest-dev/pytest-django/issues/341
            PolicyDocument.objects.create(
                type=PolicyDocumentType.TERMS_OF_SERVICE,
                content='foo',
                state='draft',
            )
            PolicyDocument.objects.create(
                type=PolicyDocumentType.PRIVACY_POLICY,
                content='foo',
                state='draft',
            )
        cls.document = PolicyDocument.objects.first()
        cls.admin = PolicyDocumentAdmin(PolicyDocument, cls.site)

    def test_save_model__calls_edit_draft(self):
        with patch.object(self.document, "edit_draft", autospec=True) as mock_edit:
            self.admin.save_model(self.request, self.document, Mock(), Mock())
            mock_edit.assert_called_once_with()

    def test_save_model__calls_publish(self):
        self.document.state = 'published'
        with patch.object(self.document, "publish", autospec=True) as mock_publish:
            self.admin.save_model(self.request, self.document, Mock(), Mock())
            mock_publish.assert_called_once_with()

    @patch('socialhome.admin.django_rq.enqueue', autospec=True)
    def test_send_email__no_selection(self, mock_enqueue):
        self.admin.send_email(self.request, PolicyDocument.objects.none())
        self.assertTrue(mock_enqueue.called is False)

    @patch('socialhome.admin.django_rq.enqueue', autospec=True)
    def test_send_email__one_selection(self, mock_enqueue):
        self.admin.send_email(self.request, PolicyDocument.objects.all()[:1])
        args, kwargs = mock_enqueue.call_args
        self.assertEqual(args[1], PolicyDocument.objects.first().type.value)

    @patch('socialhome.admin.django_rq.enqueue', autospec=True)
    def test_send_email__two_selections(self, mock_enqueue):
        self.admin.send_email(self.request, PolicyDocument.objects.all())
        args, kwargs = mock_enqueue.call_args
        self.assertEqual(args[1], 'both')
