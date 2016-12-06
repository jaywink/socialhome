from unittest import TestCase

from socialhome.content.utils import safe_text_for_markdown, safe_text, make_nsfw_safe

PLAIN_TEXT = "abcdefg kissa kävelee"
MARKDOWN_TEXT = "## header\n\nFoo Bar. *fooo*"
MARKDOWN_QUOTES_TEXT = "> foo\n> bar > foo"
SCRIPT_TEXT = "<script>console.log</script>"
MARKDOWN_CODE_TEXT = "`\n<script>alert('yup');</script>\n`\n\n`<script>alert('yup');</script>`\n\n```\n" \
                     "<script>alert('yap');</script>\n```"
HTML_TEXT = "<a href='foo'>bar</a><b>cee</b><em>daaa<div>faa</div>"


class TestSafeTextForMarkdown(object):
    def test_plain_text_survives(self):
        assert safe_text_for_markdown(PLAIN_TEXT) == PLAIN_TEXT

    def test_text_with_markdown_survives(self):
        assert safe_text_for_markdown(MARKDOWN_TEXT) == MARKDOWN_TEXT

    def test_text_with_markdown_code_survives(self):
        assert safe_text_for_markdown(MARKDOWN_CODE_TEXT) == \
               "`\n&lt;script&gt;alert('yup');&lt;/script&gt;\n`\n\n`<script>alert('yup');</script>`\n\n```\n" \
               "<script>alert('yap');</script>\n```"

    def test_text_with_script_is_cleaned(self):
        assert safe_text_for_markdown(SCRIPT_TEXT) == "&lt;script&gt;console.log&lt;/script&gt;"

    def test_text_with_html_is_cleaned(self):
        assert safe_text_for_markdown(HTML_TEXT) == '<a href="foo">bar</a><b>cee</b><em>daaa&lt;div&gt;faa&lt' \
                                                         ';/div&gt;</em>'

    def test_text_with_quotes_survives(self):
        assert safe_text_for_markdown(MARKDOWN_QUOTES_TEXT) == "> foo\n> bar &gt; foo"


class TestSafeText(object):
    def test_plain_text_survives(self):
        assert safe_text(PLAIN_TEXT) == PLAIN_TEXT

    def test_text_with_markdown_survives(self):
        assert safe_text(MARKDOWN_TEXT) == MARKDOWN_TEXT

    def test_text_with_markdown_code_is_cleaned(self):
        assert safe_text(MARKDOWN_CODE_TEXT) == "`\nalert('yup');\n`\n\n`alert('yup');`\n\n```\n" \
                                                "alert('yap');\n```"

    def test_text_with_script_is_cleaned(self):
        assert safe_text(SCRIPT_TEXT) == "console.log"

    def test_text_with_html_is_cleaned(self):
        assert safe_text(HTML_TEXT) == "barceedaaafaa"


class MakeNSFWSafeTestCase(TestCase):
    def setUp(self):
        super(MakeNSFWSafeTestCase, self).setUp()
        self.nsfw_text = '<div>FooBar</div><div><img src="localhost"/></div><div>#nsfw</div>'
        self.nsfw_text_with_classes = '<div>FooBar</div><div><img class="foobar" src="localhost"/></div>' \
                                      '<div>#nsfw</div>'
        self.nsfw_text_empty_class = '<div>FooBar</div><div><img class="" src="localhost"/></div>' \
                                     '<div>#nsfw</div>'
        self.nsfw_text_many_classes = '<div>FooBar</div><div><img class="foo bar" src="localhost"/></div>' \
                                      '<div>#nsfw</div>'

    def test_adds_nsfw_class(self):
        self.assertEqual(
            make_nsfw_safe(self.nsfw_text),
            '<div>FooBar</div><div><img class="nsfw" src="localhost"/></div><div>#nsfw</div>'
        )
        self.assertEqual(
            make_nsfw_safe(self.nsfw_text_with_classes),
            '<div>FooBar</div><div><img class="foobar nsfw" src="localhost"/></div><div>#nsfw</div>'
        )
        self.assertEqual(
            make_nsfw_safe(self.nsfw_text_empty_class),
            '<div>FooBar</div><div><img class=" nsfw" src="localhost"/></div><div>#nsfw</div>'
        )
        self.assertEqual(
            make_nsfw_safe(self.nsfw_text_many_classes),
            '<div>FooBar</div><div><img class="foo bar nsfw" src="localhost"/></div><div>#nsfw</div>'
        )
