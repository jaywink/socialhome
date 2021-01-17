import logging
from pprint import pprint

from django.core.management.base import BaseCommand
from django.db import transaction

from socialhome.content.models import Content
from socialhome.users.models import Profile

logger = logging.getLogger("socialhome")

counts = {
    "total": 0,
    "merged": 0,
    "skipped_no_public_key": 0,
    "no_dupes": 0,
    "dupes_found": 0,
    "error_saving": 0,
    "aborted_guid_handle_mismatch": 0,
    "contents_moved": 0,
    "followers_moved": 0,
    "following_moved": 0,
}

lists = {
    "merged": [],
    "error_saving": [],
    "aborted_guid_handle_mismatch": [],
}


class Command(BaseCommand):
    help = "Merge remote profiles. Attempts to merge remote profiles where the profile has both " \
           "a Diaspora protocol identifier and ActivityPub protocol identifier. The profile will be " \
           "made primarily ActivityPub. All content will be migrated to the other profile and the dupe " \
           "deleted."

    def add_arguments(self, parser):
        parser.add_argument(
            '--fid', dest='fid', default=None,
            help='Remote profile FID to look for. If not given, will look for all.',
        )
        parser.add_argument(
            '--max', dest='max', default=100,
            help='Max amount to merge, defaults to 100.',
        )

    def handle(self, *args, **options):
        max_merges = int(options["max"])
        kwargs = {
            "user__isnull": True,
            "protocol": "activitypub",
        }
        if options.get("fid"):
            kwargs["fid"] = options["fid"]

        for profile in Profile.objects.filter(**kwargs).iterator():
            counts["total"] += 1
            print(f"Checking #{profile.id}: {profile}")
            if not profile.rsa_public_key:
                print(f"   - skipping, profile has no public key")
                counts["skipped_no_public_key"] += 1
                continue

            dupes = Profile.objects.filter(
                rsa_public_key__contains=profile.rsa_public_key.strip(),
                user__isnull=True,
                protocol="diaspora",
            )
            if not dupes:
                counts["no_dupes"] += 1
                continue

            # If dupes found
            # There should only be one dupe, since we've only 2 protocols
            dupe = dupes[0]
            print(f"   - dupe found: {dupe}")
            counts["dupes_found"] += 1

            # Last check, ensure no guid / handle weirdness
            if profile.guid and profile.guid != dupe.guid:
                print(f"   - abort! {profile.guid} in the profile which does not match {dupe.guid}")
                lists["aborted_guid_handle_mismatch"].append((profile, dupe))
                counts["aborted_guid_handle_mismatch"] += 1
                continue
            if profile.handle and profile.handle != dupe.handle:
                print(f"   - abort! {profile.handle} in the profile which does not match {dupe.handle}")
                lists["aborted_guid_handle_mismatch"].append((profile, dupe))
                counts["aborted_guid_handle_mismatch"] += 1
                continue

            # Do all destructive stuff in a transaction
            try:
                with transaction.atomic():
                    # - Re-assign all content
                    for content in Content.objects.filter(author_id=dupe.id).iterator():
                        print(f"   - reassigning content: {content}")
                        content.author_id = profile.id
                        content.save()
                        counts["contents_moved"] += 1

                    # - Re-assign followers and following
                    for follower in dupe.followers.all():
                        print(f"   - reassigning follower: {follower}")
                        profile.followers.add(follower)
                        counts["followers_moved"] += 1
                    for following in dupe.following.all():
                        print(f"   - reassigning following: {following}")
                        profile.following.add(following)
                        counts["following_moved"] += 1

                    # Store info
                    profile.guid = dupe.guid
                    profile.handle = dupe.handle
                    print(f"   - setting guid {dupe.guid} and handle {dupe.handle}")

                    # delete the dupe
                    print(f"   - DELETING {dupe}")
                    dupe.delete()
                    # save the profile
                    print(f"   - SAVING {profile}")
                    profile.save()
                    counts["merged"] += 1
                    lists["merged"].append(profile)
            except Exception as ex:
                # Something failed, we've rolled back the transaction
                print(f"   - ERROR: dupe was not deleted, profile was not saved: {ex}")
                counts["error_saving"] += 1
                lists["error_saving"].append((profile, dupe))

            if counts["merged"] >= max_merges:
                print(f"\n\nReached MAX {max_merges}, aborting...")
                break

        print("\n\n-----------------------------------------------------------\n\n")
        pprint(lists)
        print("\n\n-----------------------------------------------------------\n\n")
        pprint(counts)
