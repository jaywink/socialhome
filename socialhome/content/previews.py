import datetime
import os
import re
import string
import random

from django.db import DataError
from django.db import IntegrityError
from django.db import transaction
from django.template.defaultfilters import truncatechars
from django.utils.timezone import now
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
    if not content.show_preview:
        return
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
            opengraph = OpenGraphCache.objects.get(url=url)
            Content.objects.filter(id=content.id).update(opengraph=opengraph)
            return opengraph
        try:
            og = OpenGraph(url=url, parser="lxml")
        except AttributeError:
            continue
        if not og or ("title" not in og and "site_name" not in og and "description" not in og and "image" not in og):
            continue
        try:
            title = og.title if "title" in og else og.site_name if "site_name" in og else ""
            description = og.description if "description" in og else ""
            image = og.image if "image" in og else ""
            try:
                with transaction.atomic():
                    opengraph = OpenGraphCache.objects.create(
                        url=url,
                        title=truncatechars(safe_text(title), 120),
                        description=truncatechars(safe_text(description), 500),
                        image=safe_text(image),
                    )
            except DataError:
                continue
        except IntegrityError:
            # Some other process got ahead of us
            opengraph = OpenGraphCache.objects.get(url=url)
            Content.objects.filter(id=content.id).update(opengraph=opengraph)
            return opengraph
        Content.objects.filter(id=content.id).update(opengraph=opengraph)
        return opengraph
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
                }),
                StaticDiscoveryEndpoint({
                    "schemes": [
                        "https://www.nextplatform.com/*"
                    ],
                    "url": "https://www.nextplatform.com/wp-json/oembed/1.0/embed",
                })
            ])
        ])


def fetch_oembed_preview(content, urls):
    """Fetch first oembed content for a list of urls."""
    for url in urls:
        # See first if recently cached already
        if OEmbedCache.objects.filter(url=url, modified__gte=now()-datetime.timedelta(days=7)).exists():
            oembed = OEmbedCache.objects.get(url=url)
            Content.objects.filter(id=content.id).update(oembed=oembed)
            return oembed
        # Fetch oembed
        options = {}
        if url.startswith("https://twitter.com/"):
            if len(url.split('/')) < 5:
                # Skip, not enough sections to be a tweet
                # We don't want to oembed profile streams
                continue
            # This probably has little effect since we fetch these on the backend...
            # But, DNT is always good to communicate if possible :)
            options = {"dnt": "true", "omit_script": "true"}
        try:
            oembed = PyEmbed(discoverer=OEmbedDiscoverer()).embed(url, **options)
        except (PyEmbedError, PyEmbedDiscoveryError, PyEmbedConsumerError, ValueError):
            continue
        if not oembed:
            continue
        # Keep width and height for some sites embedded videos
        video_sites = ["youtube.com", "youtu.be", "vimeo.com", "kickstarter.com"]
        if not any(site in oembed for site in video_sites):
            # Keep height if width = 100%
            if not re.search(r'\s+width="100%"', oembed):
                oembed = re.sub(r'\s+height="[0-9]+"', " ", oembed)
            # Ensure width is 100% not fixed
            oembed = re.sub(r'\s+width="[0-9]+"', ' width="100%"', oembed)
        # Wordpress sites use a random token and message events to identify the right iframe in order
        # to set the rendered height. For this to work within a masonry grid, the parent script
        # must already be loaded. Since in that context the parent script which updates the iframe
        # tag with the token is not called, we add it here.
        if "wp-embedded-content" in oembed:
            oembed = re.sub(r'<script.*</script>', '', oembed, flags=re.S)
            oembed = re.sub(r'<blockquote.*</blockquote>', '', oembed)
            ltr = string.ascii_lowercase + string.digits
            secret = ''.join(random.choice(ltr) for i in range(10))
            oembed = re.sub(r'(<iframe.*src=".*?)"', '\g<1>#?secret='+secret+'" data-secret="'+secret+'"', oembed)
        try:
            with transaction.atomic():
                oembed = OEmbedCache.objects.create(url=url, oembed=oembed)
        except IntegrityError:
            # Some other process got ahead of us
            oembed = OEmbedCache.objects.get(url=url)
            Content.objects.filter(id=content.id).update(oembed=oembed)
            return oembed
        Content.objects.filter(id=content.id).update(oembed=oembed)
        return oembed
    return False
