import logging

from django.core.management.base import BaseCommand

from socialhome.enums import Visibility
from socialhome.users.models import User, Profile

logger = logging.getLogger("socialhome")


class Command(BaseCommand):
    help = "Handle deletion of users and profiles, including content and uploaded files." \
           "Optionally lock remote profiles." \
           "!! DELETE IS PERMANENT !!"

    def add_arguments(self, parser):
        parser.add_argument(
            '--profiles', dest='profiles', default='',
            help='Remote profile FIDs to delete, separated by comma.',
        )
        parser.add_argument(
            '--lock-remote-profiles', dest='lock_remote_profiles', default=False,
            action='store_true',
            help='Give this to lock remote profiles instead of deleting them. Their'
                 'content will still be deleted locally.',
        )
        parser.add_argument(
            '--users', dest='users', default='',
            help='Local user profile UUIDs to delete, separated by comma. Deletes both user and profile.',
        )

    def handle(self, *args, **options):
        users = options['users'].split(',')
        profiles = options['profiles'].split(',')
        lock_profiles = options['lock_remote_profiles']
        self.handle_users(users)
        self.handle_profiles(profiles, lock_profiles=lock_profiles)

    def handle_users(self, users):
        for uuid in users:
            uuid = uuid.strip()
            if not uuid:
                continue
            try:
                user = User.objects.get(profile__uuid=uuid)
            except User.DoesNotExist:
                print("WARN: Could not find user with profile %s" % uuid)
                continue
            confirm = input('\n\nConfirm delete of "%s %s (%s)" (type "DELETE"): ' % (
                user.profile.name, user.username, uuid
            ))
            if confirm != 'DELETE':
                print('WARN: Skipping delete of %s' % uuid)
                continue
            try:
                user.delete()
            except Exception:
                msg = 'delete_users_and_profiles cmd: Failed to delete user %s' % user
                print(msg)
                logger.exception(msg)
            else:
                msg = 'delete_users_and_profiles cmd: Successfully delete user and their content: %s' % user
                print(msg)
                logger.info(msg)

    def handle_profiles(self, profiles, lock_profiles=False):
        for fid in profiles:
            fid = fid.strip()
            if not fid:
                continue
            try:
                profile = Profile.objects.get(fid=fid, user__isnull=True)
            except Profile.DoesNotExist:
                print("WARN: Could not find remote profile %s" % fid)
                continue

            confirm = input('\n\nConfirm delete of "%s (%s)" (type "DELETE"): ' % (
                profile.name, fid
            ))
            if confirm != 'DELETE':
                print('WARN: Skipping delete of %s' % fid)
                continue

            if lock_profiles:
                # We can't delete the profile and just let signals do the job, must iterate
                # manually :(
                for content in profile.content_set.all():
                    print('Removing local content for remote profile: %s' % content)
                    content.delete()
                # "Lock" profile by mangling public key
                profile.rsa_public_key = 'locked'
                # Hide the profile from other users
                profile.visibility = Visibility.SELF
                print('Locking remote profile: %s' % profile)
                profile.save()
                # Remove from local follower lists
                for follower in profile.followers.all():
                    print('Removing local follower %s for remote profile: %s' % (follower, profile))
                    follower.following.remove(profile)
            else:
                try:
                    profile.delete()
                except Exception:
                    msg = 'delete_users_and_profiles cmd: Failed to delete profile %s' % profile
                    print(msg)
                    logger.exception(msg)
                else:
                    msg = 'delete_users_and_profiles cmd: Successfully deleted profile and their content: %s' % profile
                    print(msg)
                    logger.info(msg)
