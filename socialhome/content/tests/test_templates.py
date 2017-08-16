from django.template.loader import render_to_string
from test_plus import TestCase


class TestBookmarkletInitial(TestCase):
    def test_template(self):
        template = render_to_string("content/_bookmarklet_initial.html", {
            "title": "a title", "url": "the url", "notes": "some notes",
        })
        self.assertEqual(template, "### a title\n\n> some notes\n\nthe url\n")
        template = render_to_string("content/_bookmarklet_initial.html", {
            "title": "a title",
        })
        self.assertEqual(template, "### a title\n")
        template = render_to_string("content/_bookmarklet_initial.html", {
            "title": "a title", "url": "the url",
        })
        self.assertEqual(template, "### a title\n\nthe url\n")
        template = render_to_string("content/_bookmarklet_initial.html", {
            "url": "the url",
        })
        self.assertEqual(template, "the url\n")
        template = render_to_string("content/_bookmarklet_initial.html", {
            "url": "the url", "notes": "some notes",
        })
        self.assertEqual(template, "> some notes\n\nthe url\n")
        template = render_to_string("content/_bookmarklet_initial.html", {
            "notes": "some notes",
        })
        self.assertEqual(template, "> some notes\n")
        template = render_to_string("content/_bookmarklet_initial.html", {
            "title": "a title", "notes": "some notes",
        })
        self.assertEqual(template, "### a title\n\n> some notes\n")
