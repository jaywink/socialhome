import datetime
import logging
from pprint import pprint

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils.timezone import make_aware

from socialhome.content.models import Content
from socialhome.users.models import Profile

import federation.utils.network as net
import federation.utils.activitypub as ap
import federation.utils.diaspora as dp
from federation.fetchers import retrieve_remote_profile

logger = logging.getLogger("socialhome")

counts = {
    "total": 0,
    "deleted": 0,
    "skipped": 0,
    "error_saving": 0,
}

lists = {
    "deleted": [],
    "skipped": [],
    "error_saving": [],
}


class Command(BaseCommand):
    help = "Delete stale remote profiles. Attempts to delete stale remote profiles. If a profile can't be " \
           "retrieved or if it has not been updated since the specified date, delete it."
    status_code = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        net.fetch_document = self._patch_status_code(net.fetch_document)
        ap.fetch_document = self._patch_status_code(ap.fetch_document)
        dp.fetch_document = self._patch_status_code(dp.fetch_document)

    def _patch_status_code(self, func):
        def wrapper(*args, **kwargs):
            document, status, error = func(*args, **kwargs)
            self.status_code = status
            return document, status, error
        return wrapper

    def add_arguments(self, parser):
        parser.add_argument(
            '--instance', dest='instance', default=None,
            help='Delete remote profiles that belong to the given instance.',
        )
        parser.add_argument(
            '--last-modified', dest='last-modified', default=None,
            help='Delete remote profiles that have not been updated since the given date. Format: YYYYMMDD.',
        )
        parser.add_argument(
            '--max', dest='max', default=100,
            help='Max amount to delete, defaults to 100.',
        )
        parser.add_argument(
            '--start-from', dest='start-from', default=None,
            help='Select the remote profiles that have been updated after the given date. Format: YYYYMMDD.',
        )

    def handle(self, *args, **options):
        instance = options["instance"]
        max_deletes = int(options["max"])
        try:
            last_modified = make_aware(datetime.datetime.strptime(options["last-modified"], "%Y%m%d"), timezone=datetime.UTC) if options["last-modified"] else None
            start_from = make_aware(datetime.datetime.strptime(options["start-from"], "%Y%m%d"), timezone=datetime.UTC) if options["start-from"] else None
        except ValueError:
            print('please use YYYYMMDD format with --last-modified')
            return
        kwargs = {
            "user__isnull": True,
        }
        args = []
        if options.get("instance"):
            args.append(Q(finger__icontains=instance)|Q(handle__icontains=instance)|Q(fid__icontains=instance))
        if options.get("last-modified"):
            kwargs["modified__lt"] = last_modified
        if options.get("start-from"):
            kwargs["modified__gte"] = start_from

        for profile in Profile.objects.filter(*args, **kwargs).order_by("modified").iterator():
            counts["total"] += 1
            no_delete = True
            if last_modified or instance: no_delete = False
            else:
                start = datetime.datetime.now()
                remote_profile = retrieve_remote_profile(profile.finger or profile.handle or profile.fid)
                end = datetime.datetime.now()
                if remote_profile: continue
                if (end-start).seconds >= 10:
                    print(f"Timeout trying to retrieve {profile} - skipping")
                    counts["skipped"] += 1
                    lists["skipped"].append(profile)
                    continue
                if self.status_code not in (None, 200, 404, 410):
                    print(f"Unexpected status code ({self.status_code}) for {profile} - skipping")
                    counts["skipped"] += 1
                    lists["skipped"].append(profile)
                    continue
                no_delete = False

            if no_delete: continue

            # Do all destructive stuff in a transaction
            try:
                with transaction.atomic():
                    print(f"Deleting #{profile.id}: {profile}, last updated: {profile.modified}, status: {self.status_code}")
                    profile.delete()

                counts["deleted"] += 1
                lists["deleted"].append(profile)
            except Exception as ex:
                # Something failed, we've rolled back the transaction
                print(f"   - ERROR: profile was not deleted: {ex}")
                counts["error_saving"] += 1
                lists["error_saving"].append((profile))

            if counts["deleted"] >= max_deletes:
                print(f"\n\nReached MAX {max_deletes}, aborting...")
                break

        print("\n\n-----------------------------------------------------------\n\n")
        pprint(lists)
        print("\n\n-----------------------------------------------------------\n\n")
        pprint(counts)
