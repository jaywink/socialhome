from socialhome.content.utils import safe_text_for_markdown_code, safe_text


PLAIN_TEXT = "abcdefg kissa kävelee"
MARKDOWN_TEXT = "## header\n\nFoo Bar. *fooo*"
SCRIPT_TEXT = "<script>console.log</script>"
MARKDOWN_CODE_TEXT = "`<script>alert('yup');</script>`\n\n```\n<script>alert('yap');</script>\n```"
HTML_TEXT = "<a href='foo'>bar</a><b>cee</b><em>daaa<div>faa</div>"


class TestSafeTextForMarkdownCode(object):
    def test_plain_text_survives(self):
        assert safe_text_for_markdown_code(PLAIN_TEXT) == PLAIN_TEXT

    def test_text_with_markdown_survives(self):
        assert safe_text_for_markdown_code(MARKDOWN_TEXT) == MARKDOWN_TEXT

    def test_text_with_markdown_code_survives(self):
        assert safe_text_for_markdown_code(MARKDOWN_CODE_TEXT) == MARKDOWN_CODE_TEXT

    def test_text_with_script_is_cleaned(self):
        assert safe_text_for_markdown_code(SCRIPT_TEXT) == "&lt;script&gt;console.log&lt;/script&gt;"

    def test_text_with_html_is_cleaned(self):
        assert safe_text_for_markdown_code(HTML_TEXT) == '<a href="foo">bar</a><b>cee</b><em>daaa&lt;div&gt;faa&lt' \
                                                         ';/div&gt;</em>'


class TestSafeText(object):
    def test_plain_text_survives(self):
        assert safe_text(PLAIN_TEXT) == PLAIN_TEXT

    def test_text_with_markdown_survives(self):
        assert safe_text(MARKDOWN_TEXT) == MARKDOWN_TEXT

    def test_text_with_markdown_code_is_cleaned(self):
        assert safe_text(MARKDOWN_CODE_TEXT) == "`alert('yup');`\n\n```\nalert('yap');\n```"

    def test_text_with_script_is_cleaned(self):
        assert safe_text(SCRIPT_TEXT) == "console.log"

    def test_text_with_html_is_cleaned(self):
        assert safe_text(HTML_TEXT) == "barceedaaafaa"
