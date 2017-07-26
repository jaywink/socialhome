from socialhome.enums import Visibility
from socialhome.tests.utils import SocialhomeTestCase
from socialhome.users.search_indexes import ProfileIndex, IntegerEnumField
from socialhome.users.tests.factories import ProfileFactory


class TestIntegerEnumField(SocialhomeTestCase):
    def test_convert(self):
        field = IntegerEnumField()
        self.assertIsNone(field.convert(None))
        self.assertEqual(field.convert(1), 1)
        self.assertEqual(field.convert(Visibility.SELF), Visibility.SELF.value)


class TestProfileIndex(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.self_profile = ProfileFactory(visibility=Visibility.SELF)
        cls.public_profile = ProfileFactory(visibility=Visibility.PUBLIC)
        cls.limited_profile = ProfileFactory(visibility=Visibility.LIMITED)
        cls.site_profile = ProfileFactory(visibility=Visibility.SITE)

    def test_index_queryset_doesnt_include_self_profiles(self):
        index = ProfileIndex()
        self.assertEqual(
            set(index.index_queryset()),
            {self.public_profile, self.limited_profile, self.site_profile}
        )
