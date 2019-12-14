from socialhome.tests.utils import SocialhomeTestCase


class TestSchemaView(SocialhomeTestCase):
    def test_page_renders(self):
        self.get("schema-redoc")
        self.response_200()
