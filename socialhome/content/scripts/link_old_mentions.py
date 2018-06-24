"""
Create a mentions link for all old content from 1 year onwards ago.
"""
import datetime

from django.utils.timezone import now

from socialhome.content.models import Content


def run(*args):
    qs = Content.objects.filter(created__gt=now() - datetime.timedelta(days=365))
    count = qs.count()
    for c, content in enumerate(qs.only('text').iterator(), 0):
        content.extract_mentions()
        if c % 1000 == 0:
            print("%s/%s" % (c, count))
