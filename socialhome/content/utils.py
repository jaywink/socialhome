import logging
import re

import bleach
import validators
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from commonmark import commonmark
from django.conf import settings
from django.urls import reverse

from federation.utils.text import find_elements, MENTION_PATTERN, TAG_PATTERN, URL_PATTERN
from socialhome.utils import get_full_url

logger = logging.getLogger("socialhome")


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
    return bleach.clean(text or "", tags=[], attributes=[], strip=True)


def find_urls_in_text(text):
    """Find url's from text.

    Beautiful does the heavy lifting here by identifying the links.

    :param text: Text to search links from
    :returns: list of urls with duplicates removed
    """
    urls = []

    soup = BeautifulSoup(commonmark(text, ignore_html_blocks=True), 'html.parser')
    for link in soup.find_all('a'):
        if link.get('data-mention') or link.get('data-hashtag'): continue
        if link.get('href') and link['href'] not in urls:
            urls.append(link['href'])
        link.extract()

    for url in find_elements(soup, URL_PATTERN):
        if url.find_parent('a'): continue
        href = url.text
        if not href.startswith('http'):
            href = 'https://' + href
        if validators.url(href) and href not in urls:
            urls.append(href)

    return urls


def process_text_links(soup: BeautifulSoup):
    """Process links in text, adding some attributes and linkifying textual links."""
    for link in soup.find_all('a', href=True):
        if link['href'].startswith('/'): continue
        if 'nofollow' not in link.get('rel', []):
            link['rel'] = ['nofollow'] + link.get('rel', [])
        link['target'] = '_blank'
        if not (link.text or link.next):
            link.string = link['href']

    for url in find_elements(soup, URL_PATTERN):
        if url.find_parent('a'): continue
        href = url.text
        if not href.startswith('http'):
            href = 'https://' + href
        if validators.url(href):
            link = soup.new_tag('a')
            link['href'] = href
            link.string = url.text
            link['rel'] = ['nofollow']
            link['target'] = '_blank'
            url.replace_with(link)


def get_and_linkify_tags(soup: BeautifulSoup):
    """Find tags in text and convert them to HTML links.

    """
    found_tags = set()
    # federation sets the data-hashtag attributes on inbound AP HTML payloads
    for link in soup.find_all('a', attrs={'data-hashtag':True}):
        tag = link['data-hashtag'].lstrip('#')
        found_tags.add(tag)
        if 'hashtag' not in link.get('class', []):
            link['class'] = ['hashtag'] + link.get('class', [])

    for tag in find_elements(soup, TAG_PATTERN):
        # ignore url fragments in link text
        final = tag.text.lstrip('#').lower()
        link = tag.find_parent('a')
        if link:
            if link.text != tag.text: continue
            if 'hashtag' not in link.get('class', []):
                link['class'] = ['hashtag'] + link.get('class', [])
        else:
            sibling = tag.previous_sibling
            if isinstance(sibling, NavigableString) and re.search(URL_PATTERN.pattern+'$', sibling): continue
            link = soup.new_tag('a')
            link.append(tag.text)
            link['class'] = 'hashtag'
            tag.replace_with(link)

        #  prepare for linkification
        found_tags.add(final)
        link['data-hashtag'] = final

    # linkify
    for link in soup.find_all('a', attrs={'data-hashtag':True}):
        link['href'] = reverse("streams:tag", kwargs={"name": link['data-hashtag']})
        del link['data-hashtag']
        link['class'] = 'hashtag'

    return found_tags


def linkify_mentions(soup: BeautifulSoup, mentions=None):
    # Linkify mentions
    # federation sets the data-mention attributes on inbound AP HTML payloads
    from federation.fetchers import retrieve_remote_profile
    from socialhome.users.models import Profile # circulars
    if not mentions: mentions = Profile.objects
    for link in soup.find_all('a', attrs={'data-mention':True}):
        mention = link['data-mention']
        try:
            profile = mentions.get(finger__iexact=mention)
        except Profile.DoesNotExist:
            remote_profile = retrieve_remote_profile(mention)
            if not remote_profile:
                continue
            profile = Profile.from_remote_profile(remote_profile)
        link['href'] = get_full_url(reverse("users:profile-detail", kwargs={"uuid": profile.uuid}))
        link['class'] = ['mention']
        del link['data-mention']

    for mention in find_elements(soup, MENTION_PATTERN):
        try:
            profile = mentions.get(finger__iexact=mention.text.lstrip('@'))
        except Profile.DoesNotExist:
            remote_profile = retrieve_remote_profile(mention.text.lstrip('@'))
            if not remote_profile:
                continue
            profile = Profile.from_remote_profile(remote_profile)
        link = soup.new_tag('a')
        link.append(mention.text)
        link['href'] = get_full_url(reverse("users:profile-detail", kwargs={"uuid": profile.uuid}))
        link['class'] = 'mention'
        mention.replace_with(link)


def update_counts(content):
    """
    Update cached data in support of threaded replies.
    This will be removed in a future release and
    replaced with a management command.
    """
    from socialhome.content.models import Content
    from socialhome.content.enums import ContentType

    if content.content_type != ContentType.CONTENT: return
    child_count = content.children.count()
    if content.reply_count == child_count or content.all_children.count() == child_count: return

    do_root = False
    for child in content.all_children.iterator():
        if child.root_parent_id != child.parent_id:
            do_root = True
            child.cache_data(commit=True)
    if do_root:
        content.cache_data(commit=True)
        content.refresh_from_db()
        logger.info(f'counts updated for content #{content.id}')
