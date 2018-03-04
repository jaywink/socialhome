from django.apps import AppConfig


class ContentConfig(AppConfig):
    name = "socialhome.content"
    verbose_name = "Content"

    def ready(self):
        """Import our signals."""
        import socialhome.content.signals
