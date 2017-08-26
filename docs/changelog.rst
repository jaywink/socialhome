.. _changelog:

Changelog
=========

[unreleased]
------------

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

* Add ``share`` endpoint to Content API. This enables creating and removing shares via the API. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)

* Allow sharing content. Clicking the share counter icon exposes a 'Share' button which when clicked will create a share. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)

* Allow unsharing content. Clicking the share counter icon exposes an 'Unshare' button (assuming the user has shared the content) which when clicked will remove the share. (`#206 <https://github.com/jaywink/socialhome/issues/206>`_)

* There is now a 'My content' stream link in the navbar 'Streams' dropdown. This goes to your own profile all content stream.

Changed
.......

* **Breaking change**. Content API results now return ``visibility`` as a string ('public', 'limited', 'site' or 'self'), not an integer.

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
