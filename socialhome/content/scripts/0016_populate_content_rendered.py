from socialhome.content.models import Content


def run(*args):
    """
    Relates to migration 0016.

    Pre-renders Content.rendered.
    """
    max_count = Content.objects.count()
    for count, content in enumerate(Content.objects.all().iterator(), 1):
        content.render()
        if count % 100 == 0:
            print("%s / %s" % (count, max_count))
