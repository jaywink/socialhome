from socialhome.content.search_indexes import TagIndex
from socialhome.content.tests.factories import ContentFactory
from socialhome.tests.utils import SocialhomeTestCase


class TestTagIndex(SocialhomeTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.content = ContentFactory(text='#foobar')

    def test_index_queryset_includes_tags_with_content(self):
        index = TagIndex()
        self.assertEqual(
            set(index.index_queryset()),
            {self.content.tags.first()}
        )
