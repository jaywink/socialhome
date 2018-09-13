from socialhome.tests.utils import SocialhomeTestCase


class TestSchemaView(SocialhomeTestCase):
    def test_page_renders(self):
        response = self.client.get("/api/")
        self.assertEqual(response.status_code, 200)
