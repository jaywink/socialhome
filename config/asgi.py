import os

from channels.asgi import get_channel_layer

from config.utils import load_local_environment

load_local_environment()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
channel_layer = get_channel_layer()
