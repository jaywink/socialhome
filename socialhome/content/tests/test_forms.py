from ddt import data, ddt
from django.test import RequestFactory

from socialhome.content.forms import ContentForm
from socialhome.content.tests.factories import PublicContentFactory, LimitedContentFactory
from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.tests.factories import UserFactory, ProfileFactory


@ddt
class TestContentForm(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = UserFactory()
        cls.profile = ProfileFactory(visibility=Visibility.PUBLIC, handle='profile1@example.com')
        cls.profile2 = ProfileFactory(visibility=Visibility.SITE, handle='profile2@example.com')
        cls.profile3 = ProfileFactory(visibility=Visibility.PUBLIC, fid='https://example.com/profile3')
        cls.profile4 = ProfileFactory(visibility=Visibility.PUBLIC, fid='diaspora://profile@example.com/profile/1234')
        cls.self_profile = ProfileFactory(visibility=Visibility.SELF, handle="self@example.com")
        cls.content = PublicContentFactory()
        cls.limited_content = LimitedContentFactory(author=cls.user.profile)
        cls.limited_content.limited_visibilities.set((cls.profile, cls.profile2))
        cls.user.profile.following.add(cls.profile2)

    def setUp(self):
        super().setUp()
        self.req = RequestFactory().get("/")
        self.req.user = self.user

    @data(
        ("profile1@example.com", True),
        ("profile1@example.com,profile2@example.com", True),
        ("https://example.com/profile3,profile2@example.com", True),
        ("https://example.com/profile3,diaspora://profile@example.com/profile/1234", True),
        ("profile1@example.com,foobar", False),
        ("self@example.com", False),
        ("foobar", False),
    )
    def test_clean__recipients(self, values):
        recipients, result = values
        form = ContentForm(
            data={"text": "barfoo", "visibility": Visibility.LIMITED.value, "recipients": recipients},
            user=self.user,
        )
        form.full_clean()
        self.assertTrue(form.is_valid() is result, values)

    def test_clean__recipients_and_include_following_cant_both_be_empty(self):
        form = ContentForm(data={"text": "barfoo", "visibility": Visibility.LIMITED.value}, user=self.user)
        form.full_clean()
        self.assertFalse(form.is_valid())

        form = ContentForm(
            data={"text": "barfoo", "visibility": Visibility.LIMITED.value, "recipients": self.user.profile.fid},
            user=self.user,
        )
        form.full_clean()
        self.assertTrue(form.is_valid())

        form = ContentForm(
            data={"text": "barfoo", "visibility": Visibility.LIMITED.value, "include_following": True},
            user=self.user,
        )
        form.full_clean()
        self.assertTrue(form.is_valid())

    @data(Visibility.SELF, Visibility.SITE, Visibility.PUBLIC)
    def test_clean__recipients_ignored_if_not_limited(self, visibility):
        form = ContentForm(
            data={"text": "barfoo", "visibility": visibility.value, "recipients": "foobar"},
            user=self.user,
        )
        form.full_clean()
        self.assertTrue(form.is_valid())

    def test_clean_text(self):
        form = ContentForm(
            data={"text": "<script>alert</script>", "visibility": Visibility.PUBLIC},
            user=self.user,
        )
        form.full_clean()
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('text'), "&lt;script&gt;alert&lt;/script&gt;")

    def test_clean_text__trusted_editor(self):
        self.user.trusted_editor = True
        form = ContentForm(
            data={"text": "<script>alert</script>", "visibility": Visibility.PUBLIC},
            user=self.user,
        )
        form.full_clean()
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data.get('text'), "<script>alert</script>")

    def test_save__collects_recipients(self):
        form = ContentForm(
            data={
                "text": "foobar",
                "visibility": Visibility.LIMITED,
                "recipients": "profile1@example.com,profile2@example.com"
            },
            user=self.user,
        )
        form.full_clean()
        self.assertTrue(form.is_valid())
        content = form.save()
        self.assertEqual(
            set(content.limited_visibilities.all()),
            {self.profile, self.profile2},
        )

    def test_save__collects_recipients__include_following(self):
        form = ContentForm(
            data={
                "text": "foobar",
                "visibility": Visibility.LIMITED,
                "recipients": "profile1@example.com",
                "include_following": True,
            },
            user=self.user,
        )
        form.full_clean()
        self.assertTrue(form.is_valid())
        content = form.save()
        self.assertEqual(
            set(content.limited_visibilities.all()),
            {self.profile, self.profile2},
        )

    def test_save__collects_recipients__reply_copies_from_parent(self):
        form = ContentForm(
            data={
                "text": "foobar",
            },
            user=self.user,
            is_reply=True,
        )
        form.full_clean()
        self.assertTrue(form.is_valid())
        content = form.save(parent=self.limited_content)
        self.assertEqual(
            set(content.limited_visibilities.all()),
            {self.profile, self.profile2},
        )

    def test_save__removes_removed_recipients(self):
        self.assertEqual(
            set(self.limited_content.limited_visibilities.all()),
            {self.profile, self.profile2},
        )
        form = ContentForm(
            data={
                "text": "foobar",
                "visibility": Visibility.LIMITED,
                "recipients": "profile1@example.com",
            },
            instance=self.limited_content,
            user=self.user,
        )
        form.full_clean()
        self.assertTrue(form.is_valid())
        content = form.save()
        self.assertEqual(
            set(content.limited_visibilities.all()),
            {self.profile},
        )

    def test_get_initial_for_field__recipients(self):
        self.assertEqual(
            set(self.limited_content.limited_visibilities.all()),
            {self.profile, self.profile2},
        )
        form = ContentForm(
            instance=self.limited_content,
            user=self.user,
        )
        initial = form.get_initial_for_field(form.fields.get('recipients'), 'recipients')
        self.assertEqual(
            set(initial.split(',')),
            {self.profile.fid, self.profile2.fid}
        )
