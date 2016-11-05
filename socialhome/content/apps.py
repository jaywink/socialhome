from django.apps import AppConfig


class ContentConfig(AppConfig):
    name = "socialhome.content"
    verbose_name = "Content"

    def ready(self):
        """Import our signals."""
        from socialhome.content.signals import notify_listeners, send_content, send_content_retraction
