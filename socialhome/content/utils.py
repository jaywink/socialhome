import re

import bleach
from bs4 import BeautifulSoup


ILLEGAL_TAG_CHARS = "!#$%^&*+.,@£/()=?`'\\{[]}~;:\"’”—\xa0"


def safe_text_for_markdown(text):
    """Clean the text using bleach but keep certain Markdown sections.

    Markdown code ie ` or ``` combos. For single `, do not allow line breaks between the tag.
    Quotes ie '> ' which bleach would clean up.
    """
    code_blocks, text = code_blocks_add_markers(text)
    # Store quotes next
    text = re.sub(r"(^> )", "%%safe_quote_in_start%%", text)
    text = re.sub(r"(\n> )", "%%safe_quote_in_new_line%%", text, flags=re.DOTALL)
    # Nuke all html, scripts, etc
    text = bleach.clean(text)
    # Return quotes
    text = text.replace("%%safe_quote_in_start%%", "> ")
    text = text.replace("%%safe_quote_in_new_line%%", "\n> ")
    text = code_blocks_restore(code_blocks, text)
    return text


def code_blocks_add_markers(text, style="markdown"):
    """Store code block contents to safety.

    :param text: Text to process
    :param style: Either 'markdown' or 'html'
    :returns: tuple (list of extracted code block texts, processed text without code block contents)
    """
    if style == "markdown":
        # Regexp match all ` and ``` pairs
        codes = re.findall(r"`(?!`)[^\r\n].*[^\r\n]`(?!`)", text, flags=re.DOTALL) + \
                re.findall(r"```.*```", text, flags=re.DOTALL)
    else:
        codes = re.findall(r"<code>.*</code>", text, flags=re.DOTALL)
    # Store to safety, replacing with markers
    safety = []
    for counter, code in enumerate(codes, 1):
        safety.append(code)
        text = text.replace(code, "%%safe_text_for_markdown codes in safety %s%%" % counter, 1)
    return safety, text


def code_blocks_restore(code_blocks, text):
    # Return ` and ``` pairs from safety
    for counter, code in enumerate(code_blocks, 1):
        text = text.replace("%%safe_text_for_markdown codes in safety %s%%" % counter, code, 1)
    return text


def safe_text(text):
    """Clean text, stripping all tags, attributes and styles."""
    return bleach.clean(text, tags=[], attributes=[], styles=[], strip=True)


def make_nsfw_safe(text):
    """Make NSFW safer by adding click-to-show class to images."""
    soup = BeautifulSoup(text, "lxml")
    images = soup.find_all("img")

    for image in images:
        if image.get("class"):
            image["class"] = "%s nsfw" % " ".join(image.get("class"))
        else:
            image["class"] = "nsfw"
        image.replace_with(image)

    result = str(soup)
    # We don't want html/body, which BeautifulSoup kindly wraps our new HTML in
    if result.startswith("<html><body>") and result.endswith("</body></html>"):
        result = result[len("<html><body>"):-len("</body></html>")]
    return result


def linkify_re_match(match):
    return '<a href="{url}" target="_blank" rel="noopener">{url}</a>'.format(url=match.group())


def linkify_text_urls(text):
    """Find textual lonely urls in the text and make them proper HTML links."""
    urls = find_urls_in_text(text)
    if not urls:
        return text
    code_blocks, text = code_blocks_add_markers(text, style="html")
    text = re.sub(
        r'^https?://[\w\./\?=#\-&_%\+~:\[\]@\!\$\(\)\*,;]*',
        linkify_re_match,
        text,
    )
    text = re.sub(
        r'(?<=[ \n]{1})https?://[\w\./\?=#\-&_%\+~:\[\]@\!\$\(\)\*,;]*',
        linkify_re_match,
        text,
    )
    text = code_blocks_restore(code_blocks, text)
    return text


def find_urls_in_text(text):
    """Find url's from text.

    URL matching by design only picks up "orphan" urls which are not href attributes or markdown links.
    There must be an empty space, line feed or text start before the url for a match to happen.

    Note, this is not entirely accurate, we're just trying to match as many as we can, allowing possibly
    a few false positives.
    """
    urls = re.findall(r'^https?://[\w\./\?=#\-&_%\+~:\[\]@\!\$\(\)\*,;]*', text) + \
           re.findall(r'(?<=[ \n]{1})https?://[\w\./\?=#\-&_%\+~:\[\]@\!\$\(\)\*,;]*', text)
    return urls


def test_tag(tag):
    """Test a word whether it could be accepted as a tag."""
    if not tag:
        return False
    for char in ILLEGAL_TAG_CHARS:
        if char in tag:
            return False
    return True
