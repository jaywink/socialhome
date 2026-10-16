import datetime

from django.core.management.base import BaseCommand
from django_dramatiq.models import Task
from django.utils.timezone import make_aware, now

from django_dramatiq.apps import DjangoDramatiqConfig

#: The database label to use when storing task metadata.
DATABASE_LABEL = DjangoDramatiqConfig.tasks_database()


class Command(BaseCommand):
    help = "Delete old django-dramatiq task records 'chunk-size' records at a time."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            '--before-date', dest='before-date', default=None,
            help='Delete tasks older than the given date. Format: YYYYMMDD.',
        )
        parser.add_argument(
            '--chunk-size', dest='chunk-size', default=1000,
            help='Max amount to delete per delete operation, defaults to 1000.',
        )

    def handle(self, *args, **options):
        chunk_size = options["chunk-size"]
        try:
            if not options["before-date"]:
                raise ValueError
            before_date = make_aware(datetime.datetime.strptime(options["before-date"], "%Y%m%d"), timezone=datetime.UTC)
        except ValueError:
            print('please use YYYYMMDD format with --before-date')
            return

        queryset = (
            Task.tasks.using(DATABASE_LABEL).filter(
                created_at__lte=before_date
            )
            .order_by()
            .values_list("pk", flat=True)
        )

        print("Deleting tasks older than", options["before-date"])
        total_deleted = 0
        while True:
            deleted, _ = Task.tasks.using(DATABASE_LABEL).filter(
                pk__in=queryset[:chunk_size]
            ).delete()
            if not deleted:
                break
            print("Deleted", deleted, "tasks")
            total_deleted += deleted

        print("Total deleted tasks:", total_deleted)
