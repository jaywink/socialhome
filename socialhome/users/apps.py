from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "socialhome.users"
    verbose_name = "Users"

    def ready(self):
        """Import our signals."""
        from socialhome.users.signals import create_user_profile, profile_following_change
