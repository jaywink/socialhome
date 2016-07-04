from socialhome.content.utils import safe_text_for_markdown_code


class TestSafeTextForMarkdownCode(object):
    PLAIN_TEXT = "abcdefg kissa kävelee"
    MARKDOWN_TEXT = "## header\n\nFoo Bar. *fooo*"
    SCRIPT_TEXT = "<script>console.log</script>"
    MARKDOWN_CODE_TEXT = "`<script>alert('yup');</script>`\n\n```\n<script>alert('yap');</script>\n```"

    def test_plain_text_survives(self):
        assert safe_text_for_markdown_code(self.PLAIN_TEXT) == self.PLAIN_TEXT

    def test_text_with_markdown_survives(self):
        assert safe_text_for_markdown_code(self.MARKDOWN_TEXT) == self.MARKDOWN_TEXT

    def test_text_with_markdown_code_survives(self):
        assert safe_text_for_markdown_code(self.MARKDOWN_CODE_TEXT) == self.MARKDOWN_CODE_TEXT

    def test_text_with_script_is_cleaned(self):
        assert safe_text_for_markdown_code(self.SCRIPT_TEXT) == "&lt;script&gt;console.log&lt;/script&gt;"
