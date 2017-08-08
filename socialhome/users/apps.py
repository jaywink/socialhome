from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "socialhome.users"
    verbose_name = "Users"

    def ready(self):
        # Import our signals
        from socialhome.users.signals import user_post_save, profile_following_change
