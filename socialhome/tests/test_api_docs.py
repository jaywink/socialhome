from socialhome.tests.utils import SocialhomeTestCase


class TestSchemaView(SocialhomeTestCase):
    def test_page_renders(self):
        self.get("api-docs")
        self.response_200()
