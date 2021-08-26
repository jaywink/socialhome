.. _changelog:

Changelog
=========

0.14.0-dev (unreleased)
-----------------------

Added
.....

Changed
.......

Fixed
.....


0.13.0 (2021-08-15)
-------------------

Added
.....

* Start adding Matrix support 🎉 Currently added functionality in this release,
  if ``SOCIALHOME_MATRIX_ENABLED`` set to ``true``:

  * Client and server well-known files are automatically generated.
  * Register local users on the configured Matrix server.
  * Post local user public posts into Matrix side to their profile timeline rooms
    and to each hashtag room.

  See docs at :ref:`matrix-protocol-support` for more information. Requires a compatible
  Matrix server running with the same server name.

* Add ``merge_remote_profiles`` management command

  Attempts to merge remote profiles where the profile has both a Diaspora protocol
  identifier and ActivityPub protocol identifier. The profile will be made primarily
  ActivityPub. All content will be migrated to the other profile and the dupe deleted.

* Translations process! Socialhome can now be translated and is now fully translated to French!
  Thanks to `tripougnif <https://git.feneas.org/tripougnif>`_ for the awesome work to both
  push through the translations process and also do the French translations <3
  Other languages partially translated are German and Norwegian. Also thanks to
  Weblate for `hosting the translations <https://hosted.weblate.org/projects/socialhome/backendfrontend/>`_
  for us.

Changed
.......

* Stop delivering public content to the Diaspora relay system by default. It's still
  possible to configure this by explicitly setting ``SOCIALHOME_RELAY_ID`` to the chosen
  relay endpoint, however by default it is now unset. Also change the default value of
  ``SOCIALHOME_RELAY_SCOPE`` from ``all`` to ``none`` (ie not subscribing to relays).

* When receiving profiles, try to match them to an existing profile using both ActivityPub
  and Diaspora protocol identifiers, to not create duplicate profiles per protocol.

* When receiving profiles, if the profile was previously set from Diaspora protocol, but
  it now also has an ActivityPub ID, switch it to be an ActivityPub profile.

Fixed
.....

* Fix share retraction towards ActivityPub platforms.

* Avoid unnecessary Profile object saves when finding sender profiles and nothing for the
  remote profile has changed.

* Stream rendering and OEembed fixes (contributed by tripougnif).

0.12.1 (2020-12-12)
-------------------

Fixed
.....

* Fix build broken by some Eslint dependencies needing update.

0.12.0 (2020-12-12)
-------------------

Added
.....

* The Content API now has full support for all visibility levels, including specifying recipients
  for limited content.

* The new publisher written in Vue is now feature complete with the current one. If you would like
  to try it out, go to your account settings and enable the new publisher. After a short trial period,
  it will become default and the old Django template code will be removed.

* Admins can now disable the Django admin error emails by setting the environment value
  ``SOCIALHOME_LOG_DISABLE_ADMIN_EMAILS=True``.

* Outbound payloads can now also be logged by toggling the relevant preference in the admin.
  When enabled, all outbound payloads will be saved for debugging purposes in the "Payloads"
  model and available via the admin.

* Fetching of unknown remote content using ActivityPub URL id's now works. Just paste the remote
  ActivityPub content URL to the search bar to fetch it from compatible platforms.

* Add a scheduled task to clean up old scheduled jobs in Redis.

* Added Django-Redisboard. This gives admins some visibility into the way Socialhome uses Redis
  via the admin pages.

Changed
.......

* Content interaction actions and icons have been fully redesigned to improve readability and to
  make it easier to interact with other peoples content. (`#574 <https://git.feneas.org/socialhome/socialhome/issues/574>`_)

  * Root level content now has "reply" and "share" actions more clearly on the left hand side of
    the content interactions area below the content text.
  * The new shares action now immediately shares (or unshares, if shared) instead of requiring
    a second action click.
  * The shares counter no longer acts as a share action.
  * Both the reply action and the replies counter expand the replies container.
  * Each reply now has a reply action as well. This is located on the right hand side of the
    content interactions area below the reply. This allows users to target their reply to
    a particular reply.
  * Replies now automatically insert mentions into the reply editor. For replies on root content,
    the root content author is mentioned. For replies on replies, both the root content author
    and the replied reply author are mentioned. The mentions can of course be removed.

  Hopefully these changes will make not only interacting easier, but also make interactions from
  Socialhome more compatible with other platforms like the microblogging side of the Fediverse.
  Feedback on these is most welcome!

* Improve rendering of outgoing mentions towards the ActivityPub network. (`#572 <https://git.feneas.org/socialhome/socialhome/issues/572>`_)

  Mentions from Socialhome now get rendered as links in outbound HTML format payloads.

* Render URL's in outgoing payloads towards the ActivityPub network as proper links. (`#572 <https://git.feneas.org/socialhome/socialhome/issues/572>`_)

* Make link preview images larger and ensure images have a title attribute.

* Stop rendering link previews for HTML style mentions that come from ActivityPub networks.

* Truncate link preview description to max 500 characters.

* Add a truncated link preview url to the link preview card.

* Don't render link preview image if the same image is already in the content text.

* OEmbed for Twitter profile streams is now skipped. Only single tweets will be embedded.

* Whitelist some more HTML tags for use in formatting content. All the tags that are purely for
  visual formatting or structuring (like div, table, dd) are now whitelisted.

* Totally rewritten publisher! The new publisher is now a part of the VueJS based frontend code and
  is based on the EasyMDE editor. There are some additional features like full-screen mode added,
  for those long blog post type content pieces. Thanks to Christophe Henry for work on this.

Fixed
.....

* Fix regression in Diaspora follows introduced in 0.11.0. Due to stricter validation
  that was added to outbound payload sending, follows to the Diaspora protocol side broke
  in 0.11.0 (from 11th of October in the development branch). All follows/unfollows during
  this period towards remote Diaspora protocol profiles have failed and should be retriggered.

* Don't crash loudly incompatible content is fetched via the Diaspora protocol fetch view and
  a document fails to validate.

* Fix an issue in the OEmbed library that caused unnecessary fetches to Spotify OEmbed
  endpoint. Thanks to Alain for reporting this issue. (`upstream issue <https://github.com/pyembed/pyembed/issues/64>`_)

* Fix rendering of quotes. Now rendered in italic and clearly marked as quote.

* Stop creating duplicate content items from remote content delivered by both ActivityPub
  and Diaspora protocols. When these refer to each other, they will be merged to avoid
  duplicate content items.

Internal changes
................

* Store an Activity on follow/unfollow. This allows retriggering follows/unfollows in
  the event of a regression.

* Move ``socialhome.content.utils.process_text_links`` to the ``federation`` library.

* Move the tags extraction logic from ``Content`` model to the ``federation`` library.

0.11.1 (2019-12-30)
-------------------

Security
........

* Upgrade Django to fix CVE-2019-19844.

Fixed
.....

* Support tag streams for non-ascii tags. (`#517 <https://git.feneas.org/socialhome/socialhome/issues/517>`_)

  Tags which fail to generate a slugified name (ie for example Russian alphabet tags) are now supported
  as streams. This also fixes the search internal server error when searching for a tag which fails to
  generate a stream URL.

0.11.0 (2019-12-15)
-------------------

Added
.....

* Searching of users on the ActivityPub protocol now works using a handle (ie ``user@domain.tld``).

* Shared content in the streams now contain the name and link to the profile of the sharer.

* Django-Silk is now available for developers to turn on for their instance.

  To turn on, set the environment variable ``SOCIALHOME_SILKY=True``.

* Users API now has an admin endpoint to return recently active users.

Changed
.......

* UI changes:

  * The stamped element (the first stream element with information about the stream or
    profile information) is now 100% wide in all situations. The profile picture has
    also been made larger.
  * The author bar has been moved from the bottom of the content to the top of the content.
  * Clicking a profile name in the author bar now pops up the author federation ID and
    reaction buttons instead of expanding them. This saves having to re-render the whole
    stream grid.

Fixed
.....

* All streams now properly push out websocket notifications on new content.

  Previously only certain streams knew how to push notifications on new content to the
  client. Now all streams will know how to do this. Additionally they will respect user
  preferences in the future when hiding of content from users is added. Shared content
  also gets a notification pushed out as other content.

* Don't process received shares if they point to a non-public content.

* Don't show a share icon for own content, unless there is a counter to show.

* Fix follow/unfollow of profiles from the search page.

* Don't raise a 500 error when Diaspora remotes try to fetch a content whose author has
  no ``handle``.

* Don't raise a 500 error when an attempt is made to view a profile with an invalid
  profile identifier

* Fix a major race issue with the ``through`` value calculation for shared content in streams (`#558 <https://git.feneas.org/socialhome/socialhome/issues/558>`_)

  When calculating ``through`` values (ie what share caused a content to appear in the stream),
  there was a race condition between processing the saved share and a remote fetched shared content.
  Values are now correctly calculates irregardless of saving order to provide correct "shared by"
  information for streams.

* Don't raise a 500 error on fetch of content using a malformed identifier

* Fix inbound federation timing issue with ActivityPub platforms (`#563 <https://git.feneas.org/socialhome/socialhome/issues/563>`_)

  Signature verification time delta check if a background worker didn't process the
  inbound payload fast enough, which led to rejected payloads. Time delta check has
  now been relaxed to allow at most 24 hour old signatures.

* Improve performance of profile streams and fetching of replies by splitting the
  database queries into multiple queries instead of one larger one. (`#562 <https://git.feneas.org/socialhome/socialhome/issues/562>`_)

API changes
...........

* **Backwards incompatible**: Removed duplicated ``user_following_author`` from the
  Content API since it is included in the serialized ``author`` as ``user_following``.

* Stream API results now contain a ``through_author`` object in the case that the content is
  in the stream via share.

* The Stream API endpoints now accept an `accept_ids` query parameter, which should be a list
  of content ID's to fetch from this particular stream. This allows filling the stream with
  new items in the stream context without making multiple fetches.

* Replaced deprecated ``django-rest-swagger`` API docs module with ``drf-yasg``. The new module
  provides not only Swagger but also ReDoc API docs. We've chosen ReDoc for the default docs
  mounted at ``/api/`` on each instance. Swagger is still available at ``/api/swagger/``. (`#537 <https://git.feneas.org/socialhome/socialhome/issues/537>`_)

Internal changes
................

* Django Channels upgraded from 1.x to 2.x version. This freed up various pinned
  dependencies like Redis and RQ to be upgraded to their latest versions. This
  also makes it unnecessary to run a Channels worker process as before. That
  has already been removed from the ``circus.ini`` file. If you run the processes
  manually, the process does not need executing any more.

0.10.0 (2019-10-06)
-------------------

Added
.....

* Initial ActivityPub support has landed!

  Basic federation support with the ActivityPub protocol. There are likely to be many
  bugs and incompatibilities with this first release which will be ironed out in the
  next few releases.

  Importantly, Socialhome defaults to ActivityPub should a remote profile support both
  ActivityPub and Diaspora protocols. This means federation across Socialhome instances
  will use ActivityPub.

  Considerable effort was put into refactoring Socialhome internals to work with multiple
  protocols. This refactoring affects mostly the internals of Socialhome with only minor
  visual changes. Some of those include changes in URL's and fallback display names for
  non-local profiles.

* Added Tags API. In addition to listing Tag objects, it allows authenticated users to follow and unfollow tags.

* Profile API now includes a list of tags followed for logged in users.

* It is now possible to follow and unfollow tags from a tag stream (`#465 <https://git.feneas.org/socialhome/socialhome/issues/465>`_)

  Content from followed tags is available under a new "Tags" stream.

* It's now possible to disable incoming `relay system <https://git.feneas.org/jaywink/social-relay>`_ integration by setting the environment variable ``SOCIALHOME_RELAY_SCOPE`` to ``none``. (`#94 <https://git.feneas.org/socialhome/socialhome/issues/94>`_)

* User profile now has a link to a new followers contacts page. This is limited to the logged in user only.

* Added a model for federation payloads for debugging purposes. If the "log all federation payloads" admin setting is on, incoming payloads will now also be available in the database via the admin pages, in addition to the log file.

Changed
.......

* **Backwards incompatible**. Python 3.6 is now the lowest supported Python version. Please do not try to upgrade Socialhome to this release before updating your Python virtualenv, if running an older Python!

* Code repository moved to the `Feneas GitLab <https://git.feneas.org/socialhome/socialhome>`_ which offers a richer set of features compared to GitHub. What is Feneas? `Check this post <https://feneas.org/hello-federation/>`_.

  Code will still be mirrored to GitHub so participation through there is still very much welcome. So you can still fork the repository on GitHub and submit a pull request. Issues however will be available only on the GitLab server to avoid these getting out of sync between the servers.

* The behaviour of the ``delete_users_and_profiles`` management command has been changed to lock remote profiles by default instead of deleting them. This is more efficient for spam control as deleted profiles just appear back. The lock option can still be set as false to delete the profile which is a good option for example when cleaning data of remote profiles on request.

* **Breaking change**. API changes. (`#451 <https://git.feneas.org/socialhome/socialhome/issues/451>`_)

  * Profile API has been migrated to use UUID's instead of ID's.

    All API endpoints will be receiving this change which is done while the API has a limited number of consumers and will be one of the last planned breaking changes planned before a 1.0 API can be announced.

  * Profile API following and unfollowing endpoints have changed.

    The action ``add_follower`` has been renamed to ``follow`` and ``remove_follower`` to ``unfollow``. The change reflects the change of the endpoints themselves. Now to add a follower one does a POST to the ``follow`` of the profile that one wants to follow, instead of doing a POST to the ``add_follower`` endpoint of ones own profile. Same change has been done for the follower removal endpoint.

  * Streams profile API's have moved to using UUID's instead of ID's.

* Make profile default visibility public (`#515 <https://git.feneas.org/socialhome/socialhome/issues/515>`_)

  This fixes an issue where new profiles can follow others but the others cannot follow back, since the default was SELF. For now, make all new profiles public by default. Later the visibility setting should be moved from the profile to profile fields themselves. Some core identity will always need to be public but what the profile shares could be controlled.

  Also make remote profiles always locally public to avoid situations where a user can see the post but can't see the local profile. Any profile that federates to us is public to some extent since it left the server.

* Global search now works also with ActivityPub ID's to fetch a remote profile

* Added a few additional HTML elements to content cleanup whitelist: tags `span, p, br` and attribute `class` on `span`.

Fixed
.....

* API docs regression fixed (`#509 <https://github.com/jaywink/socialhome/issues/509>`_)

* Fix internal server error for anonymous user for certain internal user pages (`#518 <https://git.feneas.org/socialhome/socialhome/issues/518>`_)

* Timeout of the pre-calculated stream cache cleanup job has been extended so that it doesn't timeout on larger servers.

* Nested replies are now correctly shown as replies to the root level content instead of being hidden from view.

* Removed unnecessary federation of replies to local root authors.

* Removed quick reply possibility for non-public content. This fixes an issue of non-public replies created with the quick reply editor not federating.

  While the API support is being added needed by the quick reply editor for non-public content, only the full editor can be used for non-public replies.

* Fix retraction of limited visibility content sent out to the federation layer.

  There was a bug where limited visibility content (added in 0.9.0) retractions were not sent out correctly. This was caused by the usage of the Django ``post_delete`` signal to handle the retraction. This works for public content since all the information is present immediately after the delete for the background jobs, even if the database entry has been deleted. Unfortunately for limited content this did not work since they store visibilities to the limited content in a separate table. Due to the (awesome!) way Django relations work, the entries for the visibilities got deleted from the database before the ``post_delete`` signal got fired.

  Content retraction is now fired off into a background task in the Django ``pre_delete`` hook, which means the limited visibilities data is still available in the database.

Internal changes
................

* Removed ``User`` relationship fields. These were migrated to ``Profile`` a long time ago.
* Heavy refactoring of Vue frontend store.
* Django bumped to 2.2.

0.9.3 (2018-08-29)
------------------

Fixed
.....

* Update ``pycryptodome`` due to CVE-2018-15560 security issue.

0.9.2 (2018-08-11)
------------------

Fixed
.....

* Update to ``federation`` which switches crypto libraries to fix CVE-2018-6594.

  **Note!** If you don't use ``pip-sync`` to deploy, then you **must** do ``pip uninstall pycrypto`` before deploying, or things will break badly.

0.9.1 (2018-08-11)
------------------

Fixed
.....

* Django bumped to 2.0.8 to fix a `security issue <https://docs.djangoproject.com/en/2.0/releases/2.0.8/>`_. This issue did not affect Socialhome, but we're upgrading just to be sure.

0.9.0 (2018-07-21)
------------------

Added
.....

* Add possibility to configure Sentry for error reporting.

  Adding the Sentry project DSN as ``SENTRY_DSN=foo`` to environment variables will make all error level exceptions be raised to Sentry. To change the level, define ``SENTRY_LEVEL`` with a valid Python logging module level.

* Add `NodeInfo2 <https://github.com/jaywink/nodeinfo2>`_ support. For organization details, admin name and email will be published if the new setting ``SOCIALHOME_SHOW_ADMINS`` is set to ``True`` (default ``False``).

* Add possibility to delete user account (`#131 <https://github.com/jaywink/socialhome/issues/131>`_)

  Deletion is permanent and will delete all created content including uploaded images. Delete request for profile
  and related content will be sent to remote servers.

* Add user export API (`#478 <https://github.com/jaywink/socialhome/issues/478>`_)

  New API endpoints ``/api/profiles/create_export/`` will create an export and ``/api/profiles/retrieve_export/`` will retrieve the export zip file. Export will contain a JSON file of the user, profile, followers and content. A zip file of uploaded images will also be included.

* Add user data export to user account page (`#478 <https://github.com/jaywink/socialhome/issues/478>`_)

  The account page now has a button to request an export of user data. In addition to user and profile data, this export contains a list of profiles followed, content (including shares and replies) and a zip file of image uploads. An email notification will be sent to the user once the export is ready for download from the account page.

* New environment variable ``DJANGO_TIMEZONE`` allows easily customizing the time zone that the Socialhome instance runs on. It defaults to ``UTC``.

* Staff users can now access the admin and task queue (background jobs) pages via the new "gears" menu in the navbar. See <`documentation <https://socialhome.readthedocs.io/en/latest/running.html#admin-user>`_ on how to make a user admin.

* Add an easily customizable ``robots.txt`` with default rules

  The rules by default disallow all except direct links to content, the root profile and the public stream. Server admins can customize the rules easily via the admin interface.

* Admins can now add Terms of Service and Privacy Policy documents to the site (`#477 <https://github.com/jaywink/socialhome/issues/477>`_)

  Terms of Service and Privacy policy documents are good to have. These tell people visiting your site what rules you operate with. Socialhome provides default templates you can activate with a few clicks.

  To review and enable the policy documents, log in as admin and access the admin pages through the navigation bar cogs menu. Scroll down and locate "Policy documents". There are two types of documents, the Terms of Service and Privacy Policy. Each one can be edited in draft mode and then published. Further updates in draft mode will not overwrite the last published version, until published.

  To publish the documents, open them, review the text and then change the status below the document to "published". Click Save - this version is now published. To edit in draft mode, switch the status back and the current edited revision will not show to users. You can also send email updates to users from the policy documents list. Select the policy documents you wish the send an email about, choose "Send email" from the actions list and confirm.

  Published policy documents are shown to both authenticated and unauthenticated users via the navigation bar cogs menu.

* Searching for hashtags is now possible using the global search

  The global search now in addition to profile results returns also results of matching hashtags. If the search term includes the hash ('#') and matches exactly to a tag, an instant redirect will be made to the tag stream.

* Mentions are now parsed out of incoming remote content and locally created content.

  Currently the only syntax supported is the Diaspora mentions syntax, ie ``@{Name; user@domain.tld}``. Currently Socialhome users can create mentions by using the syntax manually. UI layer will be added later to choose people using the standard @ syntax to trigger search.

  When mentioned, local users will be sent an email notification with a link to the content.

  **Note to admins**: A script is provided if you want to parse old content for mentions. Run ``./manage.py runscript link_old_mentions`` if you wish to parse the content from the last year and create the links. This will also send out email notifications.

* Admin now has a section for Content items and Profiles, for debugging purposes. The User admin was also improved.

* Limited content is now supported 🙈 💪 (`#302 <https://github.com/jaywink/socialhome/issues/302>`_)

  Limited content can now be created using the web create form. Note, API does not currently allow creating limited content (except replies to limited content). Once create form is ported to the API, things should be refactored there, right now had no bandwidth to ensure both work.

  Limited content is shown in the stream with a lock symbol. The create shows some extra fields for limited content. These include "recipients" and "include following". Recipients is a comma separated list of target profile handles the limited content will be sent to. Include following will populate recipients (on save) with all the profiles that one follows. Later on we will add contact lists for better targeting.

  Limited content visibilities can be edited. If someone is removed from the target recipients, a retraction will be sent to try and delete the content remotely from the target recipient.

  Currently recipients must already be known to the server, in the future a remote search will be done if the profile is not known. Any known remote profile can be targeted - it is up to the receiving server to decide whether to accept it or not. For local profiles, those of visibility SELF (ie hidden) cannot be targeted.

  There is also a new stream "Limited" available. It shows all limited content visible to you.

* Add "Local" stream which contains only content from users registered on the same server. (`#491 <https://github.com/jaywink/socialhome/issues/491>`_)

Changed
.......

* Bump Django to 2.0 🎉 (`#460 <https://github.com/jaywink/socialhome/issues/460>`_)

* Only precache for users who have been active (`#436 <https://github.com/jaywink/socialhome/issues/436>`_)

  Don't precache items into streams for users who have not been active. Controlled by the same settings as the maintenance of precached streams. Will reduce unnecessary background jobs and make Redis memory usage even more stable.

* Provided Circus configuration now ensures RQ worker processes are not allowed to endlessly hog server memory. In some rare cases it has happened that normally very stable RQ worker processes have hogged several gigabytes of memory due to reasons which are still being investigated. Now Circus will end those processes automatically.

* Moved user account, logout, email management and API token pages links under the new "gears" menu in the navbar. These links used to be in the profile page menu.

Fixed
.....

* Allow search with Diaspora handle that contains port (`#457 <https://github.com/jaywink/socialhome/issues/457>`_)

* **Important for server admins**. There was a mistake in the production Redis connection settings. The setting was not following the given configuration in the documentation. Now the possibility to set ``REDIS_URL`` (undocumented) directly has been removed and will raise an error. Use the ``REDIS_HOST``, ``REDIS_DB``, ``REDIS_PORT`` and ``REDIS_PASSWORD`` settings instead when needed.

* Ensure all streams Redis keys have a default expiry of 30 days.

* Fix parsing of remote profile names by also using ``last_name`` attribute, where given (`#414 <https://github.com/jaywink/socialhome/issues/414>`_)

* Show possible validation errors on create form instead of just not allowing a save.

* Fix failure of processing remote retractions of replies or shares in some situations.

Removed
.......

* Legacy streams routes `/public/`, `/followed/` and `/tags/<name>/` have been removed. They already partially broke in the Vue.js streams rewrite.

0.8.0 (2018-03-06)
------------------

Added
.....

* RFC7033 webfinger support for Diaspora protocol (`#405 <https://github.com/jaywink/socialhome/issues/405>`_)

  This allows better profile discovery by remote non-Socialhome servers.

* Added better streams precache maintenance in regards to inactive users (`#436 <https://github.com/jaywink/socialhome/issues/436>`_)

  Two new settings have been added:

  * ``SOCIALHOME_STREAMS_PRECACHE_INACTIVE_DAYS`` (default 90)
  * ``SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE`` (default 0)

  If a user has been more than the set days without logging in, when trimming the precaches for that user, the inactive setting will be used instead. By default this means that precaches for users that haven't logged in for 90 days are removed. This is done to ensure Redis memory usage is predictable and stable in relation to active users.

  Users who have been inactive for longer than the X days will still get their stream content normally but instead of getting a fast stream render from the cache, the items will be calculated using databse queries, which produces a slower stream load experience.

* Added management command to delete local users and remote profiles

  This allows removing users who want their account to be deleted (coming to UI soon, sorry) and also deleting content and locking remote spam accounts. See `documentation <https://socialhome.readthedocs.io/en/latest/running.html>`_ for details.

Changed
.......

* Setting ``SOCIALHOME_RELAY_DOMAIN`` is now called ``SOCIALHOME_RELAY_ID``. We're slowly replacing all direct Diaspora handle references with Diaspora URI format profile ID's in preparation for ActivityPub protocol addition.

  No action needed from server admins unless you have changed this setting, in which case it should be updated accordingly.

* Start sending profile changes to remote nodes as public messages for better efficiency

* Start sending federation payloads in new format (`federation #59 <https://github.com/jaywink/federation/issues/59>`_)

  This could drop federation compatibility with some really old servers in the fediverse, but adds compatibility to for example GangGo which is now able to receive Socialhome content.

* Stop requesting Twitter widget script for each tweet OEmbed (`#202 <https://github.com/jaywink/socialhome/issues/202>`_)

  Since Vue streams all tweets are initialized programmatically as they are rendered in the stream so we don't need to have the script tag on each oembed separately.

* ``/api-token-auth/`` endpoint now returns limited profile information in addition to token

Fixed
.....

* Fix precached streams maintenance job. (`#436 <https://github.com/jaywink/socialhome/issues/436>`_)

  Due to mistake in regexp not all old precached stream items were pruned in maintenance. Now fixed which should ensure Redis memory usage does not suffer from unreasonable increase over time.

* Fix profile discovery from current stable Diaspora (`#413 <https://github.com/jaywink/socialhome/issues/413>`_)

  A bug in Diaspora caused Socialhome profile discovery to fail. Introduce some patches to our webfinger to work around the bug and make profiles available to latest Diaspora versions.

* Fix receiving public content from GangGo (`federation #115 <https://github.com/jaywink/federation/issues/115>`_)

* Fix various errors in search for remote profiles

  For example GNU Social implements webfinger but the necessary attributes we need are not present and were causing errors.

* Add missing titles and OG tags back to streams (`#428 <https://github.com/jaywink/socialhome/issues/428>`_)

  These disappeared in the rewrite of streams in 0.7.0. Also added a few new head tags improving author information in single content view and telling Twitter to not track users so much.

0.7.0 (2018-02-04)
------------------

New Vue.js frontend
...................

The work that started at a small hackathon in Helsinki in July 2017 is finally finished! The old buggy and hard to maintain Django template + jQuery based frontend has been completely rewritten in Vue.js. This provides a modern frontend code base, making it possible to add new features faster and to spend less time fixing bugs in the spaghetti code.

A huge thanks goes out to @christophehenry doing most of the work in pushing this rewrite through!

Added
.....

* Possibility to skip adding an OEmbed or OpenGraph preview to content. (`#364 <https://github.com/jaywink/socialhome/issues/364>`_)

  There is a new checkbox on content create that allows skipping adding a link preview to the content.

* Add maintenance job to groom precache information from Redis. This ensures Redis memory usage stays stable.

  **Important for server admins**. There is a new process to run that is responsible for scheduling these maintenance jobs. The process is executed as a Django management command ie ``python manage.py rqscheduler``.
    * If you already use the `provided Circus configuration <https://socialhome.readthedocs.io/en/latest/installation/ubuntu.html#set-up-circus>`_ to run Socialhome, you **don't need to do anything**. When you restart Socialhome, the updated Circus configuration will automatically be used and the scheduler process started by Circus.
    * If you have a custom setup, preferring to run all processes manually, ensure one ``rqscheduler`` process is running at all times to ensure maintenance jobs and other future scheduled jobs are executed.

   A new configuration item ``SOCIALHOME_STREAMS_PRECACHE_SIZE`` is available to set the maximum size of precached stream items per user, per stream. This defaults to 100 items. Increasing this setting can radically increase Redis memory usage. If you have a lot of users, you might consider decreasing this setting if Redis memory usage climbs up too high.

* It is now possible to use email for log-in. (`#377 <https://github.com/jaywink/socialhome/issues/377>`_)

* Added a Code of Conduct document. All contributors to Socialhome are expected to honour these simple rules to ensure our project is a safe place to contribute to.

  Read the Code of Conduct `here <https://github.com/jaywink/socialhome/blob/master/CODE_OF_CONDUCT.md>`_.

* Profile API has 4 new read only fields:

  * ``followers_count`` - Count of followers the given Profile has. For remote profiles this will contain only the count of followers on this server, not all the followers the profile has.
  * ``following_count`` - Count of local and remote profiles this Profile is following. For remote profiles this will contain only the count of profiles following this profile on this particular server.
  * ``has_pinned_content`` - Boolean indication whether the local profile has pinned any Content to their profile stream. Always false for remote profiles.
  * ``user_following`` - Boolean whether logged in user is following the profile.

* There is now a management command to generate dummy content for development environment purposes. See :ref:`development` pages.

* Installation docs now have an example SystemD service configuration, see :ref:`installation-other-systemd`. (`#397 <https://github.com/jaywink/socialhome/issues/397>`_)

* Content API has a new read only field ``has_twitter_oembed``. This is ``true`` if the content text had a Tweet URL *and* a fetch for the OEmbed code has been successfully made.

* Content create page now has an option to disable federating to remote servers when saving the content. (`#296 <https://github.com/jaywink/socialhome/issues/296>`_)

  The content will still update to local streams normally. Federating the content can be enabled on further saves.

* If signups are closed, the signup link will now stay active but will point to a list of Socialhome nodes. (`#354 <https://github.com/jaywink/socialhome/issues/354>`_)

  By default this URL is https://the-federation.info/socialhome, but can be configured by the server admin.

Changed
.......

* When processing a remote share of local content, deliver it also to all participants in the original shared content and also to all personal followers. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)

* Allow creating replies via the Content API.

  Replies are created by simply passing in a ``parent`` with the ID value of the target Content. It is not possible to change the ``parent`` value for an existing reply or root level Content object once created. When creating a reply, you can omit ``visibility`` from the sent data. Visibility will be used from the parent Content item automatically.

* Removed Opbeat integration related configuration. The service is being ramped down. (`#393 <https://github.com/jaywink/socialhome/issues/393>`_)

  If as a server administrator you have enabled Opbeat monitoring, it will stop working on this update.

* New VueJS stream is now default \o/ (`#202 <https://github.com/jaywink/socialhome/issues/202>`_)

  Old stream can still be accessed using the user preferences or by passing a `vue=0` parameter in the URL. All existing users have been migrated to use the new VueJS streams by default.

Fixed
.....

* Redirect back to profile instead of home view after organize pinned content save action. (`#313 <https://github.com/jaywink/socialhome/issues/313>`_)

* Fix searching of an unknown remote profile by handle using uppercase letters resulting in an invalid local profile creation.

* Fix Content querysets not correctly including the 'through' information which tells what content caused a share to be added to a stream. (`#412 <https://github.com/jaywink/socialhome/issues/412>`_)

  This information was already correctly added in the streams precalculation phase, but if the cache started cold or a viewing user cycled through all cached content ID's and wanted some more, the database queries did not return the right results.

* Attempt to fetch OEmbed and OpenGraph previews of URL's in content in the order of the links found. (`#365 <https://github.com/jaywink/socialhome/issues/365>`_)

  Previous behaviour lead to fetching previews of urls in random order, leading to a different url preview on different Socialhome servers.

* Fix remote profile retrieval from remote servers which don't support legacy Diaspora protocol webfinger. (`#405 <https://github.com/jaywink/socialhome/issues/405>`_)

  New version of federation library defaults to trying the new style webfinger with a fall back to legacy.

0.6.0 (2017-11-13)
------------------

Added
.....

* Profile "All content" streams now include the shares the profile has done. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)
* Streams API now has endpoints for profile streams to match the profile streams in the UI. (`#194 <https://github.com/jaywink/socialhome/issues/194>`_)

  * ``/api/streams/profile-all/{id}/`` - fetches all content by the given profile (including shares), ordered by created date in reverse order (= new stuff first).
  * ``/api/streams/profile-pinned/{id}/`` - fetches pinned content by the given profile, ordered as set by the profile owner.

* New fields added to Content API:

  * ``is_nsfw``, boolean value, ``true`` if the content text has the tag ``#nsfw`` in it.
  * ``share_of``, if the ``content_type`` is ``share``, this will contain the ID of the shared Content.

* If an incoming share references a remote target that doesn't yet exist locally, it and the author profile will be fetched and imported over the network. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)

* There are now Docker files for doing development work for Socialhome. See the docs `here <https://socialhome.readthedocs.io/en/latest/development.html#developing-with-docker>`_.

* Third-party applications can now be added to enhance Socialhome or replace some of the core functionality, using configuration. The following new settings are available:

  * ``SOCIALHOME_ADDITIONAL_APPS`` - List of additional applications to use in Django settings.
  * ``SOCIALHOME_ADDITIONAL_APPS_URLS`` - Additional third-party URL's to add to core url configuration.
  * ``SOCIALHOME_HOME_VIEW`` - Override the home view with another view defined with this setting.

* Content API now has a new ``shares`` endpoint. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)

  This allows retrieving all the shares done on a Content.

* We now have a logo ✌

  .. image:: _static/brand/Socialhome-dark-300.png

  The logo also comes in a light version, for dark backgrounds. See :ref:`brand` for details.

Changed
.......

* Logging configuration changes:

  * Removed separate logfile for the federation loggers. Now all logs go to one place. Setting ``SOCIALHOME_LOGFILE_FEDERATION`` has been removed.
  * Added possibility to direct Django and application logs using a defined level to syslog. Adds three settings, ``SOCIALHOME_LOG_TARGET`` to define whether to log to file or syslog, ``SOCIALHOME_SYSLOG_LEVEL`` to define the level of syslog logging and ``SOCIALHOME_SYSLOG_FACILITY`` to define the syslog logging facility. See `configuration <https://socialhome.readthedocs.io/en/latest/running.html#configuration>`_ documentation.

* **Important!** The file to place configuration environment variables has changed to ``.env``.

  This is a more standard file name for environment variables than the previous ``env.local``. For now we'll still load from the old file too, but a warning will be displayed to rename the file.

* **Breaking change**. API ``Content`` serialization now returns list of tags as *name of tag*, not ID as before. The names do not contain the character "#".

* Content API ``replies`` endpoint now includes all the replies on the shares of the Content too.

* Use modified timestamp for created timestamp when federating out to remote nodes. (`#314 <https://github.com/jaywink/socialhome/issues/314>`_)

  This makes edits federate more reliably to some remote platforms that support edits.

* Stream grid item reply icon changed from "envelope" to "comments". (`#339 <https://github.com/jaywink/socialhome/issues/339>`_)

Fixed
.....

* Fix various issues with OpenGraph tags parsing by switching to self-maintained fork of ``python-opengraph``.
* Share button is no longer visible if not signed in (`#325 <https://github.com/jaywink/socialhome/issues/325>`_)
* Remote profile image urls that are relative are now fixed to be absolute when importing the profile from remote (`#327 <https://github.com/jaywink/socialhome/issues/327>`_)
* Fix poor performance of fetching replies.

  When adding replies of shares to the collection of replies fetched when clicking the reply icon in the UI, a serious performance regression was also added. Database queries have now been optimized to fetch replies faster again.
* When editing a reply, the user is now redirected back to the parent content detail view instead of going to the reply detail view. (`#315 <https://github.com/jaywink/socialhome/issues/315>`_)
* Fix regression on visibility of remote replies on shares.

  Replies inherit the parent object visibility and share visibility defaults to non-public in the federation library. Diaspora protocol removed the ``public`` property from shares in a recent release, which meant that we started getting all shares as non-public from the federation layer. This meant that all comments on the shares were processed as non-public too.

  With a change in the federation layer, Diaspora protocol shares are now public by default.

* Fixed Streams API content ``user_is_author`` value always having ``false`` value.

0.5.0 (2017-10-01)
------------------

Python dependencies
...................

Switched to ``pip-tools`` as the recommended way to install Python dependencies and cleaned the requirements files a bit. Now all the "base" dependencies, including production deployment dependencies are locked in ``requirements.txt``. The new file ``dev-requirements.txt`` includes both the base and the extra development/testing related dependencies.

To use ``pip-tools``, first install it:

::

    pip install -U pip-tools

Then install dependencies:

::

    # Production environment
    pip-sync

    # Development environment
    pip-sync dev-requirements.txt

It is not mandatory to use ``pip-tools`` for running a production installation. For development it is mandatory. All dependencies should be placed (unlocked) in either ``requirements/requirements.in`` (base) or ``requirements/requirements-dev.in`` (development extras). Then execute ``./compile-requirements.sh`` to update the locked dependency files after each change to the ``.in`` files. See `pip-tools <https://github.com/jazzband/pip-tools>`_ for more information.

Added
.....

* GIF uploads are now possible when creating content or replies. (`#125 <https://github.com/jaywink/socialhome/issues/125>`_)

* Content API has a new endpoint ``/api/content/<id>/replies/``. This returns all the replies for the given content.

* Shares made by followed contacts are now pulled up to the "Followed" stream.

  This happens only if the user has not already seen this content in their "Followed" stream. Each content should only appear once, either directly by following the author or a followed contact sharing the content. Multiple shares do not raise the content in the stream again.

Changed
.......

* Rendered link processing has been rewritten. This fixes issues with some links not being linkified when rendering. Additionally now all external links are made to open in a new tab or window. (`#197 <https://github.com/jaywink/socialhome/issues/197>`_)

* Previously previews and oEmbed's for content used to only pick up "orphan" links from the content text. This meant that if there was a Markdown or HTML link, there would be no link preview or oEmbed fetched. This has now been changed. All links found in the content will be considered for preview and oEmbed. The first link to return a preview or oEmbed will be used.

* Streams URL changes:

    * All streams will now be under ``/streams/`` for a cleaner URL layout. So for example ``/public/`` is now ``/streams/public/``.
    * Tag stream URL has been changed from ``/streams/tags/<tag>/`` to ``/streams/tag/<tag>/``. This small change allows us to later map ``/stream/tags/`` to the tags the user is following.

  Since lots of old content will point to the old URL's, there will be support for the legacy URL's until they are needed for something else in the future.

* **Breaking change**. Profile API field changes:

    * Added:

        * ``url`` (Full URL of local profile)
        * ``home_url`` (Full URL of remote profile, if remote user)
        * ``is_local`` (Boolean, is user local)
        * ``visibility`` (Profile visibility setting, either ``public``, ``limited``, ``site`` or ``self``. Editable to self)

    * Removed (internal attributes unnecessary for frontend rendering):

        * ``user``
        * ``rsa_public_key``

* **Breaking change**. Content API field changes:

    * Added:

        * ``timestamp`` (ISO 8601 formatted timestamp of last save)
        * ``humanized_timestamp`` (For example "2 hours ago")
        * ``url`` (Full URL to content detail)
        * ``edited`` (Boolean whether content has been edited since creation)
        * ``user_following_author`` (Boolean whether current user is following content author)
        * ``user_is_author`` (Boolean whether current user is the author of the content)
        * ``user_has_shared`` (Boolean whether current user has shared the content)

    * Changed:

        * ``author`` is now a limited serialization of the author profile, containing the following keys: "guid", "handle", "home_url", "id", "image_url_small", "is_local", "name", "url".

          The reason for serializing the author information to content is related to privacy controls. A user who maintains a limited profile can still create public content, for example. A user who is able to view the content created by the user should also see some limited information about the creating profile. To get the full profile, the user needs to fetch the profile object by ID, which is subject to the visibility set by the profile owner.

    * Removed (internal attributes unnecessary for frontend rendering):

        * ``created``
        * ``modified``
        * ``oembed``
        * ``opengraph``

* Refactoring for streams views to use new Stream classes which support pre-caching of content ID's. No visible changes to user experience except a faster "Followed users" stream.

  A stream class that is set as cached will store into Redis a list of content ID's for each user who would normally see that content in the stream. This allows pulling content out of the database very fast. If the stream is not cached or does not have cached content ID's, normal database lookups will be used.

  This refactoring enables creating more complex streams which require heavier calculations to decide whether a content item should be in a stream or not.

Fixed
.....

* Cycling browser tabs with CTRL-TAB when focused on the editor no longer inserts a TAB character in the editor.
* Don't federate shares to shared content local author. This caused unnecessary deliveries between the same host.

0.4.0 (2017-08-31)
------------------

Update notes
............

This release contains long running migrations. Please allow up to 10 minutes for the migrations to run, depending on your database size.

Added
.....

* Allow user to change profile picture. (`#151 <https://github.com/jaywink/socialhome/issues/151>`_)

  Profile menu now has an extra option "Change picture". This allows uploading a new picture and optionally setting focus point for cropping a picture that is not square shape.

* Federate local profiles to remote followers on save. (`#168 <https://github.com/jaywink/socialhome/issues/168>`_)

* Process remote profiles entities on receive.

  Remote profiles were so far only created on first encounter. Now we also process incoming ``Profile`` entities from the federation layer.

* When following a remote profile, federate profile to them at the same time.

* It is now possible to expose statistics from a Socialhome node. This includes counts for users (total, 30 day, 6 month), local content and local replies. These will be exposed via the ``NodeInfo`` documents that for example `the-federation.info <https://the-federation.info>`_ node list consumes.

  By default statistics is off. Admins can switch the counts on by setting environment variable ``SOCIALHOME_STATISTICS=True`` and restarting Socialhome.

* Add user API token view. Allows retrieving an API token for usage in clients and tools. Allows also regenerating the token if it has been lost or exposed.

* Added bookmarklet to easily share external pages. The bookmarklet can be bookmarked from the 'Create' page. (`#138 <https://github.com/jaywink/socialhome/issues/138>`_)

  Sharing with the bookmarklet will copy the page url, title and optionally selected text into the create content text area. The bookmarklet is compatible with Diaspora, so for example the Firefox `sharing service <https://activations.cdn.mozilla.net/en-US/diaspora.html>`_ will work.

* Support receiving 'Share' entities. Show amount of shares on content. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)

* Show replies to shares on the original shared content. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)

* Add ``share`` endpoint to Content API. This enables creating and removing shares via the API. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)

* Allow sharing content. Clicking the share counter icon exposes a 'Share' button which when clicked will create a share. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)

* Allow unsharing content. Clicking the share counter icon exposes an 'Unshare' button (assuming the user has shared the content) which when clicked will remove the share. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)

* Federate local shares to remote nodes. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)

* There is now a 'My content' stream link in the navbar 'Streams' dropdown. This goes to your own profile all content stream.

* Add user preference for the new stream refactoring. If enabled, all streams that have a new version in progress will be rendered with the new frontend code based on Vue.js. (`#202 <https://github.com/jaywink/socialhome/issues/202>`_)

  Warning! The new frontent code doesn't have all the features of the current on yet.

* Content API has three new read only fields available:

    * ``local``, boolean whether the content is local or remote.
    * ``reply_count``, count of replies (including replies on shares)
    * ``shares_count``, count of shares

* Make email notifications nicer by using HTML templates in addition to the plain text version. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)

  In addition to reply and follow notifications, send also when own content is shared.

Changed
.......

* **Breaking change**. Content API results now return ``visibility`` as a string ('public', 'limited', 'site' or 'self'), not an integer.

Fixed
.....

* There was no notification sent out when a local user followed a local user. This has now been fixed.

Removed
.......

* **Breaking change**. Removed Content, Profile and Users API LIST routes. For now these are seen as not required for building a client and allow unnecessarily easy data mining.

* Removed content modal. Clicking timestamp in grid now directly loads the content detail view. (`#162 <https://github.com/jaywink/socialhome/issues/162>`_)

  Loading the content in a modal was an early experiment and didn't end out very usable.

* Removed reply button from replies. Technically, threaded replies are possible but the UI implementation is not done. Replying to a reply will be back once UI and federation layer will handle threaded replies properly.

0.3.1 (2017-08-06)
------------------

Fixed
.....

* Bump ``federation`` library again to fix a regression in reply relaying due to security fixes in the library 0.14.0 release.


0.3.0 (2017-08-06)
------------------

Security
........

* Reject remote content updates via the federation layer which reference an already existing remote content object but have a different author.

  Note that locally created content was previously safe from this kind of takeover. This, even though serious, affects only remote created content stored locally.

* Reject remote reply updates via the federation layer which try to change the parent content reference.

* Bump `federation <https://github.com/jaywink/federation/releases/tag/v0.14.0>`_ to ensure remote entity authorship is verified correctly.

Added
.....

* API has two new endpoints, the "Content" and "Image Upload" routes. (`#120 <https://github.com/jaywink/socialhome/issues/120>`_)

    * Content API allows browsing content objects that are visible to self, or public for anonymous users. Content objects owned by self can be updated or deleted. Creating content is also possible.
    * Image Upload API allows uploading images via the same mechanism that is used in the content create UI form. The uploaded image will be stored and a markdown string is passed back which can be added to content created in for example mobile clients. Note, uploading an image doesn't create any content itself, it just allows embedding images into content, just like in the UI.

* New API docs exposed by Django REST Swagger. These are in the same place as the old ones, at ``/api/``. Adding to the documentation is still a work in progress.
* Add image upload button to the create/reply editor. This makes it possible to upload images from mobile browsers. (`#120 <https://github.com/jaywink/socialhome/issues/120>`_)
* Make profile "following" button link to "following contacts" page, if user is logged in and own profile.

Changed
.......

* Create and update content will now redirect to the content created or updated. Previous behaviour was user preferred landing page.
* Delete content will now redirect back to the page where the delete was triggered from. Previous behaviour was user preferred landing page. If the content delete is triggered from the content detail page, redirect will happen to user preferred landing page as before. (`#204 <https://github.com/jaywink/socialhome/issues/204>`_)

Fixed
.....

* Fix internal server error when replying to content that contained only characters outside the western Latin character sets.
* Visual fixes for content rendering in content delete page.
* Make direct profile handle search survive extra spaces before or after the searched handle.

0.2.1 (2017-07-30)
------------------

Fixed
.....

* Fix reply form regression introduced in v0.2.0. (`#217 <https://github.com/jaywink/socialhome/issues/217>`_)

0.2.0 (2017-07-30)
------------------

Security
........

* Fix XSS vulnerability in profile edit. Unsanitized profile field input was allowed and one place showed a field without escaping it. The fields are now sanitized and escaping has been ensured.

  The problem concerned only local users and not remote profile fields which were correctly sanitized already.

Added
.....

* Added search for profiles (`#163 <https://github.com/jaywink/socialhome/issues/163>`_)

  There is now a global search in the right side of the header. The search returns matches for local and remote profiles based on their name and username part of the handle. Profiles marked with visibility ``Self`` or ``Limited`` are excluded from the search results. Profiles marked with visibility ``Site`` will be excluded if not logged in, leaving only public profile results. If a direct match happens with a full handle, a redirect is done directly to the searched profile.

  **IMPORTANT for node maintainers**. After pulling in this change, you MUST run the command ``python manage.py rebuild_index`` to create the search index. Not doing this will cause an error to be raised when trying to search. The indexes are kept up to date automatically after running this command once.

* When searching for profiles based on handle, fetch profile from remote if it isn't found locally (`#163 <https://github.com/jaywink/socialhome/issues/163>`_)

Changed
.......

* Improved content/reply create/edit form. Replies don't contain visibility or pinned form elements any more. Added also some help texts regarding drag'n'drop image embed, visibility and content pinning.

Fixed
.....

* Make reply notifications to local users not send one single email with all local participants, but one email per participant. Previous implementation would have leaked emails of participants to other participants.
* Correctly send replies to remotes (`#210 <https://github.com/jaywink/socialhome/issues/210>`_)

  If parent content is local, send via the relayable forwarding mechanism. This ensures parent author signs the content. If parent author is remote, send just to the remote author. The remote author should then relay it.
* Ensure calling ``Profile.private_key`` or ``Profile.key`` don't crash if the profile doesn't have keys. Now the properties just return ``None``.
* Fix regression in profile all content stream load more functionality. (`#190 <https://github.com/jaywink/socialhome/issues/190>`_)
* Filter out "limited" visibility profiles from API list results. These profiles are not available in the search so they shouldn't be available to list through the API either.

0.1.0 (2017-07-27)
------------------

Initial versioned release. Main implemented features:

* Working streams (followed, public, profiles)
* Content creation
* Content OEmbed / OpenGraph previews
* Replies
* Follow/unfollow of profiles
* Contacts list
* Pinning content to profile
