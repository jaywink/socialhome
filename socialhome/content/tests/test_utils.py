from django.test import TestCase

from socialhome.content.utils import (
    safe_text_for_markdown, safe_text, find_urls_in_text)

PLAIN_TEXT = "abcdefg kissa kävelee"
MARKDOWN_TEXT = "## header\n\nFoo Bar. *fooo*"
MARKDOWN_QUOTES_TEXT = "> foo\n> bar > foo"
SCRIPT_TEXT = "<script>console.log</script>"
MARKDOWN_CODE_TEXT = "`\n<script>alert('yup');</script>\n`\n\n`<script>alert('yup');</script>`\n\n```\n" \
                     "<script>alert('yap');</script>\n```"
HTML_TEXT = "<a href='foo'>bar</a><b>cee</b><em>daaa<div><span class='jee'>faa</span></div>"
HTML_TEXT_WITH_MENTION_LINK = '<p><span class="h-card"><a href="https://dev.jasonrobinson.me/u/jaywink/" ' \
                              'class="u-url mention">@<span>jaywink</span></a></span> boom</p>'


class TestSafeTextForMarkdown:
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
        assert safe_text_for_markdown(HTML_TEXT) == '<a href="foo">bar</a><b>cee</b><em>daaa<div><span ' \
                                                    'class="jee">faa</span></div></em>'

    def test_text_with_html_is_cleaned__mention_link_classes_preserved(self):
        assert safe_text_for_markdown(HTML_TEXT_WITH_MENTION_LINK) == \
           '<p><span class="h-card"><a href="https://dev.jasonrobinson.me/u/jaywink/" class="u-url mention"' \
           '>@<span>jaywink</span></a></span> boom</p>'

    def test_text_with_quotes_survives(self):
        assert safe_text_for_markdown(MARKDOWN_QUOTES_TEXT) == "> foo\n> bar &gt; foo"


class TestSafeText:
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
        assert safe_text(HTML_TEXT) == "barceedaaa\nfaa"

    def test_text_with_html_is_cleaned__mention_link_removed(self):
        assert safe_text(HTML_TEXT_WITH_MENTION_LINK) == '@jaywink boom'


class TestFindUrlsInText(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.starts_with_url = "https://example.com/foobar"
        cls.http_starts_with_url = "http://example.com/foobar"
        cls.numbers = "http://foo123.633.com"
        cls.special_chars = "https://example.com/~@!$()*,;_%20+wat.wot?foo=bar&bar=foo#rokkenroll"
        cls.urls_in_text = "fewfe https://example1.com grheiugheriu\nhttps://example2.com " \
                           "fhuiwehfui https://example-3.com\nfwfefewjuio"
        cls.href_and_markdown = "foo <a href='https://example.com'>bar</a> " \
                                "<a href=\"https://example.net\">bar</a>" \
                                "[waat](https://example.org)"
        cls.without_protocol = "example.org"
        cls.many_for_ordered = "http://spam.com http://eggs.com http://spam.com"
        cls.with_mention = '<a href="https://example.com" class="mention">foo</a> https://example.net'

    def test_ignores_mention(self):
        urls = find_urls_in_text(self.with_mention)
        self.assertEqual(urls, ["https://example.net"])

    def test_returns_in_order_without_duplicates(self):
        urls = find_urls_in_text(self.many_for_ordered)
        self.assertEqual(urls, ["http://spam.com", "http://eggs.com"])

    def test_starts_with_url(self):
        urls = find_urls_in_text(self.starts_with_url)
        self.assertEqual(urls, [self.starts_with_url])
        urls = find_urls_in_text(self.http_starts_with_url)
        self.assertEqual(urls, [self.http_starts_with_url])

    def test_numbers(self):
        urls = find_urls_in_text(self.numbers)
        self.assertEqual(urls, [self.numbers])

    def test_special_chars(self):
        urls = find_urls_in_text(self.special_chars)
        self.assertEqual(urls, [self.special_chars])

    def test_urls_in_text(self):
        urls = find_urls_in_text(self.urls_in_text)
        self.assertEqual(urls, [
            "https://example1.com", "https://example2.com", "https://example-3.com"
        ])

    def test_href_markdown(self):
        urls = find_urls_in_text(self.href_and_markdown)
        self.assertEqual(urls, ["https://example.com", "https://example.net", "https://example.org"])

    def test_without_protocol(self):
        urls = find_urls_in_text(self.without_protocol)
        self.assertEqual(urls, ["http://example.org"])
