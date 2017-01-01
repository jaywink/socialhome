import datetime
import os
import re

from django.db import DataError
from django.db import IntegrityError
from django.utils.timezone import now
from django_extensions.utils.text import truncate_letters
from opengraph import OpenGraph
from pyembed import core as pyembedcore  # Ugh, but pyembed itself doesn't have a __file__ attr
from pyembed.core import PyEmbed, PyEmbedError
from pyembed.core.consumer import PyEmbedConsumerError
from pyembed.core.discovery import (
    UrlDiscoverer, PyEmbedDiscoveryError, ChainingDiscoverer, FileDiscoverer, StaticDiscoveryEndpoint,
    StaticDiscoverer
)

from socialhome.content.models import Content, OEmbedCache, OpenGraphCache
from socialhome.content.utils import safe_text, find_urls_in_text


def fetch_content_preview(content):
    """Fetch a preview or oEmbed for a content.

    Will first try to fetch oEmbed for each found url.
    If not available, generate a preview from the OG tags.
    """
    urls = find_urls_in_text(content.text)
    if not urls:
        return
    preview_done = fetch_oembed_preview(content, urls)
    if not preview_done:
        fetch_og_preview(content, urls)


def fetch_og_preview(content, urls):
    """Fetch first opengraph entry for a list of urls."""
    for url in urls:
        # See first if recently cached already
        if OpenGraphCache.objects.filter(url=url, modified__gte=now() - datetime.timedelta(days=7)).exists():
            Content.objects.filter(id=content.id).update(opengraph=OpenGraphCache.objects.get(url=url))
            return True
        # OpenGraph is kinda broken - make sure we destroy any old data before fetching
        OpenGraph.__data__ = {}
        try:
            og = OpenGraph(url=url)
        except ConnectionError:
            continue
        if not og or (not "title" in og and not "site_name" in og and not "description" in og and not "image" in og):
            continue
        try:
            title = og.title if "title" in og else og.site_name if "site_name" in og else ""
            description = og.description if "description" in og else ""
            image = og.image if "image" in og else ""
            try:
                opengraph = OpenGraphCache.objects.create(
                    url=url,
                    title=truncate_letters(safe_text(title), 250),
                    description=safe_text(description),
                    image=safe_text(image),
                )
            except DataError:
                continue
        except IntegrityError:
            # Some other process got ahead of us
            Content.objects.filter(id=content.id).update(opengraph=OpenGraphCache.objects.get(url=url))
            return True
        Content.objects.filter(id=content.id).update(opengraph=opengraph)
        return True
    return False


class OEmbedDiscoverer(ChainingDiscoverer):
    """DefaultDiscoverer without the auto discovery."""
    def __init__(self):
        super().__init__([
            FileDiscoverer(os.path.join(
                os.path.dirname(pyembedcore.__file__), "config", "providers.json"
            )),
            UrlDiscoverer('http://oembed.com/providers.json'),
            StaticDiscoverer(endpoints=[
                StaticDiscoveryEndpoint({
                    "schemes": [
                        "https://twitter.com/"
                    ],
                    "url": "https://publish.twitter.com/oembed",
                })
            ])
        ])


def fetch_oembed_preview(content, urls):
    """Fetch first oembed content for a list of urls."""
    for url in urls:
        # See first if recently cached already
        if OEmbedCache.objects.filter(url=url, modified__gte=now()-datetime.timedelta(days=7)).exists():
            Content.objects.filter(id=content.id).update(oembed=OEmbedCache.objects.get(url=url))
            return True
        # Fetch oembed
        try:
            oembed = PyEmbed(discoverer=OEmbedDiscoverer()).embed(url)
        except (PyEmbedError, PyEmbedDiscoveryError, PyEmbedConsumerError, ValueError):
            continue
        if not oembed:
            continue
        # Ensure width is 100% not fixed
        oembed = re.sub(r'width="[0-9]*"', 'width="100%"', oembed)
        oembed = re.sub(r'height="[0-9]*"', "", oembed)
        try:
            oembed = OEmbedCache.objects.create(url=url, oembed=oembed)
        except IntegrityError:
            # Some other process got ahead of us
            Content.objects.filter(id=content.id).update(oembed=OEmbedCache.objects.get(url=url))
            return True
        Content.objects.filter(id=content.id).update(oembed=oembed)
        return True
    return False
