from django.apps import AppConfig


class SocialhomeConfig(AppConfig):
    name = "socialhome"
    verbose_name = "Socialhome"

    def ready(self):
        # Import our signals
        import socialhome.signals
