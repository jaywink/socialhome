from django.conf import settings


def get_full_media_url(path):
    return "{url}{media}{path}".format(
        url=settings.SOCIALHOME_URL, media=settings.MEDIA_URL, path=path,
    )
