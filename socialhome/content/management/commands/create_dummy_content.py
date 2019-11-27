from random import shuffle

from django.core.management.base import BaseCommand

from socialhome.content.tests.factories import PublicContentFactory
from socialhome.users.models import Profile, User


class Command(BaseCommand):
    help = "Create dummy content."

    def add_arguments(self, parser):
        parser.add_argument("--amount", type=int, help="Amount to create, defaults to 100.", default=100)
        parser.add_argument("--user-email", type=str,
                            help="Provide an email for which a number of contact will be created", default=None)

    def handle(self, *args, **options):
        """Create dummy content."""
        for i in range(options["amount"]):
            content = PublicContentFactory()
            print("Created content: %s" % content)

        user_email = options["user_email"]
        if user_email is not None:

            user = User.objects.get(email=user_email)
            if user is None:
                print("Error: no user with email {0} found").format(user_email)
            else:
                all_profiles = Profile.objects.exclude(uuid=user.profile.uuid)[::1]
                count = len(all_profiles)
                nb_contacts = min(count, 500)

                shuffle(all_profiles)
                user.profile.following.add(*all_profiles[:nb_contacts])
                print("Added %s contacts to %s's followed contacts" % (nb_contacts, user_email))

                shuffle(all_profiles)
                profiles = all_profiles[:nb_contacts]
                [profile.following.add(user.profile) for profile in profiles]
                print("Added %s contacts to %s's followers" % (nb_contacts, user_email))
