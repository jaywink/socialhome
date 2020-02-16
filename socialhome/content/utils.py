import re

import bleach
from bleach import callbacks
from django.conf import settings

ILLEGAL_TAG_CHARS = "!#$%^&*+.,@£/()=?`'\\{[]}~;:\"’”—\xa0"


def safe_text_for_markdown(text: str) -> str:
    """Clean the text using bleach but keep certain Markdown sections.

    Markdown code ie ` or ``` combos. For single `, do not allow line breaks between the tag.
    Quotes ie '> ' which bleach would clean up.
    """
    code_blocks, text = code_blocks_add_markers(text)
    # Store quotes next
    text = re.sub(r"(^> )", "%%safe_quote_in_start%%", text)
    text = re.sub(r"(\n> )", "%%safe_quote_in_new_line%%", text, flags=re.DOTALL)
    # Nuke all html, scripts, etc
    text = bleach.clean(
        text or "",
        tags=settings.SOCIALHOME_CONTENT_SAFE_TAGS,
        attributes=settings.SOCIALHOME_CONTENT_SAFE_ATTRS,
    )
    # Return quotes
    text = text.replace("%%safe_quote_in_start%%", "> ")
    text = text.replace("%%safe_quote_in_new_line%%", "\n> ")
    text = code_blocks_restore(code_blocks, text)
    return text


def code_blocks_add_markers(text):
    """Store code block contents to safety.

    :param text: Text to process
    :returns: tuple (list of extracted code block texts, processed text without code block contents)
    """
    # Regexp match all ` and ``` pairs
    codes = re.findall(r"`(?!`)[^\r\n].*[^\r\n]`(?!`)", text, flags=re.DOTALL) + \
            re.findall(r"```.*```", text, flags=re.DOTALL)
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
    return bleach.clean(text or "", tags=[], attributes=[], styles=[], strip=True)


def process_text_links(text):
    """Process links in text, adding some attributes and linkifying textual links."""
    link_callbacks = [callbacks.nofollow, callbacks.target_blank]

    def link_attributes(attrs, new=False):
        """Run standard callbacks except for internal links."""
        href_key = (None, "href")
        if attrs.get(href_key).startswith("/"):
            return attrs

        # Run the standard callbacks
        for callback in link_callbacks:
            attrs = callback(attrs, new)
        return attrs

    return bleach.linkify(
        text,
        callbacks=[link_attributes],
        parse_email=False,
        skip_tags=["code"],
    )


def find_urls_in_text(text):
    """Find url's from text.

    Bleach does the heavy lifting here by identifying the links.

    :param text: Text to search links from
    :returns: list of urls with duplicates removed
    """
    urls = []

    def link_collector(attrs, new=False):
        if "mention" in attrs.get((None, "class"), []):
            return
        url = attrs.get((None, "href"))
        if url not in urls:
            urls.append(url)

    bleach.linkify(text, callbacks=[link_collector], parse_email=False, skip_tags=["code"])
    return urls


def test_tag(tag):
    """Test a word whether it could be accepted as a tag."""
    if not tag:
        return False
    for char in ILLEGAL_TAG_CHARS:
        if char in tag:
            return False
    return True
