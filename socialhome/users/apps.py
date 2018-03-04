from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "socialhome.users"
    verbose_name = "Users"

    def ready(self):
        # Import our signals
        import socialhome.users.signals
