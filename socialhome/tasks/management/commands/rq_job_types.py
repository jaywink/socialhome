import json
from collections import defaultdict

import django_rq
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = """List count of distinct job types currently queued."""

    def handle(self, *args, **options):
        def default_number():
            return 0

        job_types = defaultdict(default_number)

        # Currently there is only One Queue
        queue = django_rq.get_queue()
        print(f"Current total count: {queue.count}")
        print("Job types:")
        for job in queue.get_jobs():
            job_type = job.description.split('(')[0]
            job_types[job_type] += 1

        job_types = dict(sorted(job_types.items(), key=lambda x: -x[1]))
        print(json.dumps(job_types, indent=2))
