from django.core.management.base import BaseCommand

from socialhome.content.tests.factories import PublicContentFactory


class Command(BaseCommand):
    help = "Create dummy content."

    def add_arguments(self, parser):
        parser.add_argument("--amount", type=int, help="Amount to create, defaults to 100.", default=100)

    def handle(self, *args, **options):
        """Create dummy content."""
        for i in range(options["amount"]):
            content = PublicContentFactory()
            print("Created content: %s" % content)
