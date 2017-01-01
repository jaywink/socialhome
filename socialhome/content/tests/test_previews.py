from django.test import TestCase


class FetchOgPreviewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(FetchOgPreviewTestCase, cls).setUpTestData()

    def setUp(self):
        super(FetchOgPreviewTestCase, self).setUp()

    def test_og_does_not_remember_old_values(self):
        # TODO
        pass
