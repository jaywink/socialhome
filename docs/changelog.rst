.. _changelog:

Changelog
=========

0.6.0-dev (unreleased)
----------------------

Added
.....

* Profile "All content" streams now include the shares the profile has done. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)
* Streams API now has endpoints for profile streams to match the profile streams in the UI. (`#194 <https://github.com/jaywink/socialhome/issues/194>`_)

  * ``/api/streams/profile-all/{id}/`` - fetches all content by the given profile (including shares), ordered by created date in reverse order (= new stuff first).
  * ``/api/streams/profile-pinned/{id}/`` - fetches pinned content by the given profile, ordered as set by the profile owner.

* API ``Content`` serialization now includes an ``is_nsfw`` boolean. This is ``true`` if the content text has the tag ``#nsfw`` in it.

* If an incoming share references a remote target that doesn't yet exist locally, it and the author profile will be fetched and imported over the network. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)

* There are now Docker files for doing development work for Socialhome. See the docs `here <https://socialhome.readthedocs.io/en/latest/development.html#developing-with-docker>`_.

* Third-party applications can now be added to enhance Socialhome or replace some of the core functionality, using configuration. The following new settings are available:

  * ``SOCIALHOME_ADDITIONAL_APPS`` - List of additional applications to use in Django settings.
  * ``SOCIALHOME_ADDITIONAL_APPS_URLS`` - Additional third-party URL's to add to core url configuration.
  * ``SOCIALHOME_HOME_VIEW`` - Override the home view with another view defined with this setting.
* Vue streams: streams load more content on scroll (`#346 <https://github.com/jaywink/socialhome/pull/346>`_)

Changed
.......

* Logging configuration changes:

  * Removed separate logfile for the federation loggers. Now all logs go to one place. Setting ``SOCIALHOME_LOGFILE_FEDERATION`` has been removed.
  * Added possibility to direct Django and application logs using a defined level to syslog. Adds three settings, ``SOCIALHOME_LOG_TARGET`` to define whether to log to file or syslog, ``SOCIALHOME_SYSLOG_LEVEL`` to define the level of syslog logging and ``SOCIALHOME_SYSLOG_FACILITY`` to define the syslog logging facility. See `configuration <https://socialhome.readthedocs.io/en/latest/running.html#configuration>`_ documentation.

* **Important!** The file to place configuration environment variables has changed to ``.env``.

  This is a more standard file name for environment variables than the previous ``env.local``. For now we'll still load from the old file too, but a warning will be displayed to rename the file.

* **Breaking change**. API ``Content`` serialization now returns list of tags as *name of tag*, not ID as before. The names do not contain the character "#".

Fixed
.....

* Fix various issues with OpenGraph tags parsing by switching to self-maintained fork of ``python-opengraph``.
* Share button is no longer visible if not signed in (`#325 <https://github.com/jaywink/socialhome/issues/325>`_)

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
