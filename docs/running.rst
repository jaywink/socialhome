.. _running:

Running an instance
===================

Some notes on running a production instance.

Django admin
------------

The normal Django admin can be found at ``/admin``.

.. _shell:

Executing the Django shell
--------------------------

Assuming included installation instructions were used, do the following:

::

    sudo su - socialhome
    workon socialhome
    cd socialhome
    python manage.py shell_plus

.. _shell-email-confirm:

Confirming user emails via the shell
------------------------------------

You can manually confirm user emails via the shell by running the following:

::

    from allauth.account.models import EmailAddress
    EmailAddress.objects.filter(email=<email>).update(verified=True)

This will allow the user to log in without clicking the confirmation email link.

.. _admin-user:

Admin user
----------

To make a user an admin, log in to the shell and execute the following to set the user as superuser:

::

    from socialhome.users.models import User
    User.objects.filter(username=<username>).update(is_staff=True, is_superuser=True)

Backups
-------

Three places should be backed up from the Socialhome instance to ensure recovery in the event of a disaster.

* The database
* Local settings in ``.env`` (assuming you are using this way to configure the application)
* The path ``socialhome/media/`` which contains for example image uploads
* The Redis database (`example instructions <https://www.digitalocean.com/community/tutorials/how-to-back-up-and-restore-your-redis-data-on-ubuntu-14-04>`_)

Give your instance some visibility
----------------------------------

If you want some public visibility to your instance, consider registering it at some lists that track nodes in "The Federation". Here are a few:

* https://the-federation.info
* https://podupti.me

Why not also contribute to the numbers of the federated social web? Turn on :ref:`configuration-statistics` to expose some activity counts.

Log files
---------

There are two main logs where Socialhome sends information during runtime.

* Circus process log

  Rotated log files in ``/var/log/upstart/socialhome-circus.log``. The location will differ if not using an Upstart based system.

  This log contains the output of all the processes required to run Socialhome, if using the recommended way of running Socialhome using Circus. Any errors for example when starting uWSGI or the worker processes will be found here.

* Application log

  See :ref:`config-log-target` configuration value. This log contains logging entries from the application itself. Useful for debugging federation issues or other problems with the actual code.

.. _delete-user-or-profile:

Deleting users and locking remote profiles
------------------------------------------

To delete users and their content, a Django management command has been provided. This command can also be used to delete local content of remote profiles and optionally lock the profile so any new content is rejected. This makes it possible to lock out spam accounts for example. For locally created content, an automatic retraction will be sent to remotes.

NOTE! Any deletion is **permanent**. There is no possibility to get the data back, except by restoring database and uploaded file backups. Be sure before using the command and be extra sure about the UUID's passed in!

To delete a local user, run the command as follows:

::

   python manage.py delete_users_and_profiles --users <uuid>

To delete a remote profile, run the command as follows:

::

   python manage.py delete_users_and_profiles --profiles <uuid>

To only delete remote profile content and then lock the profile, run as follows:

::

   python manage.py delete_users_and_profiles --profiles <uuid> --lock-remote-profiles

Multiple ``uuid``'s can be passed in by separating them with commas. A confirmation dialog is produced for each user or profile to be deleted.

.. _policy-docs:

Policy documents
----------------

Terms of Service and Privacy policy documents are good to have. These tell people visiting your site what rules you operate with. Socialhome provides default templates you can activate with a few clicks.

To review and enable the policy documents, log in as admin and access the admin pages through the navigation bar cogs menu. Scroll down and locate "Policy documents". There are two types of documents, the Terms of Service and Privacy Policy. Each one can be edited in draft mode and then published. Further updates in draft mode will not overwrite the last published version, until published.

To publish the documents, open them, review the text and then change the status below the document to "published". Click Save - this version is now published. To edit in draft mode, switch the status back and the current edited revision will not show to users. You can also send email updates to users from the policy documents list. Select the policy documents you wish the send an email about, choose "Send email" from the actions list and confirm.

Published policy documents are shown to both authenticated and unauthenticated users via the navigation bar cogs menu.

.. _matrix-protocol-support:

Matrix protocol support
-----------------------

*Note! Extremely alpha, work on progress, non-functional*

After getting excited about `Cerulean <https://matrix.org/blog/2020/12/18/introducing-cerulean>`_, work has
started to integrate the Matrix protocol into Socialhome. While for Diaspora and ActivityPub protocols, Socialhome
is fully in server mode, for Matrix we will be taking a different route. Making Socialhome into a full homeserver
would be overkill to integrate Socialhome with the Matrix network, so instead Socialhome will become a multi-person
client towards other Matrix servers.

To run Socialhome with Matrix support, you will need to also run a `Dendrite <https://github.com/matrix-org/dendrite>`_
server. This should be a dedicated instance for Socialhome alone as it will be tightly integrated.
NOTE! Currently only Denrite v0.3.11 has been properly tested against.

When setting up the Dendrite server currently the following assumptions are made:

* the server name is the domain of the Socialhome instance (for example ``domain.tld``)
* the homeserver is reachable via ``matrix.domain.tld`` port 443. Socialhome will handle the
  well-known delegation for you.

Once you have this Dendrite running, you can set ``SOCIALHOME_MATRIX_ENABLED`` to ``true``.

Current functionality:

* Client and server well-known files are automatically generated.
* Register local users on the configured Matrix server.
* Post local user public posts into Matrix side to their profile timeline rooms
  and to each hashtag room.

.. _configuration:

Configuration
-------------

Configuration mainly happens through environment variables. Those are passed to Django via the file ``.env`` in the repository root. The following items of note can be changed.

After making changes to this file, don't forget to reload the app with ``sudo service socialhome restart``.

DATABASE_URL
............

Default: ``postgres:///socialhome``

This must be set to a proper database URL, for example ``postgres://socialhome:DATABASEPASSWORDHERE@127.0.0.1:5432/socialhome``.

DJANGO_ACCOUNT_ALLOW_REGISTRATION
.................................

Default: ``True``

Set this to ``False`` if you want to disable signups.

DJANGO_ADMIN_MAIL
.................

Default: ``info@socialhome.local``

Admin email for terms of service and privacy policy documents, outgoing emails and server metadata.

DJANGO_ADMIN_NAME
.................

Default: ``Socialhome Admin``

Admin display name or organization name for Terms of Service, outgoing emails and server metadata.

DJANGO_ALLOWED_HOSTS
....................

Default: ``socialhome.local``

Domain that is used for this instance. Must be set to the right domain. Note, it's not a good idea to use a sub-domain wildcard for www, ie ``.`` as per Django docs. Federated sites work better with only one absolute domain.

.. _email-config:

DJANGO_EMAIL_BACKEND
....................

Default: ``django.core.mail.backends.console.EmailBackend``

Must be set to some real email backend if you wish to send emails. See `docs <https://docs.djangoproject.com/en/2.2/ref/settings/#email-backend>`_ for backend options and additional configuration help.

The possible other email related additional settings are as follows. Please see Django documentation link above for details.

* ``DJANGO_EMAIL_HOST`` (default ``localhost``)
* ``DJANGO_EMAIL_PORT`` (default ``587``)
* ``DJANGO_EMAIL_HOST_USER`` (default '')
* ``DJANGO_EMAIL_HOST_PASSWORD`` (default '')
* ``DJANGO_EMAIL_USE_TLS`` (default ``True``)
* ``DJANGO_EMAIL_USE_SSL`` (default ``False``)
* ``DJANGO_EMAIL_TIMEOUT`` (default '')
* ``DJANGO_EMAIL_SSL_KEYFILE`` (default '')
* ``DJANGO_EMAIL_SSL_CERTFILE`` (default '')
* ``DJANGO_EMAIL_SUBJECT_PREFIX`` (default ``[Socialhome]``)
* ``DJANGO_DEFAULT_FROM_EMAIL`` (default ``noreply@socialhome.local``)
* ``DJANGO_SERVER_EMAIL`` (defaults to ``DJANGO_DEFAULT_FROM_EMAIL`` value)

Note, email *is* required for signing up. Users will **not** be able to sign up if the instance does not have working email sending.

DJANGO_SECRET_KEY
.................

Default: ''

Must be set to a long secret string. Don't expose it to anyone. See `docs <https://docs.djangoproject.com/en/dev/ref/settings/#secret-key>`_

DJANGO_SECURE_CONTENT_TYPE_NOSNIFF
..................................

Default: ``True``

See `docs <https://django-secure.readthedocs.io/en/latest/settings.html#secure-content-type-nosniff>`_.

DJANGO_SECURE_FRAME_DENY
........................

Default: ``True``

See `docs <https://django-secure.readthedocs.io/en/latest/settings.html#secure-frame-deny>`_.

DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS
.....................................

Default: ``True``

See `docs <https://docs.djangoproject.com/en/1.11/ref/settings/#secure-hsts-include-subdomains>`_.

DJANGO_SECURE_SSL_REDIRECT
..........................

Default: ``True``

Redirect all requests to HTTPS. See `docs <https://django-secure.readthedocs.io/en/latest/settings.html#secure-ssl-redirect>`_.

DJANGO_TIMEZONE
...............

Default: ``UTC``

REDIS_DB
........

Default: ``0``

REDIS_HOST
..........

Default: ``localhost``

REDIS_PASSWORD
..............

Default: ''

REDIS_PORT
..........

Default: ``6379``

SENTRY_DSN
..........

Default: ``None``

Setting a Sentry project DSN will make all error level exceptions be raised to Sentry. To change the level, see below.

SENTRY_LEVEL
............

Default: ``ERROR``

Logging level used for Sentry reporting (see above). Possible options: ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``.

SOCIALHOME_ADDITIONAL_APPS
..........................

Default: ``None``

Allows to plug in additional third-party apps, string with comma-separated values, for example ``django.contrib.gis,myapp``.

SOCIALHOME_ADDITIONAL_APPS_URLS
...............................

Default: ``None``

Allows to use additional third-party app url-conf, string with two comma-separated values, url prefix and path to urlpatterns, for example ``myapp/,myapp.urls``.
If you need to include urls from more than one app, this could be done by creating intermediary app which aggregates urls.

SOCIALHOME_DOMAIN
.................

Default: ``socialhome.local``

Must be set to your Socialhome instance domain. Used for example to generate outbound links.

SOCIALHOME_HOME_VIEW
.....................

Default: ``None``

Allows to use on main page custom view from third-party app, string with path to view, for example ``myapp.views.AwesomeHomeView``.

SOCIALHOME_HTTPS
................

Default: ``True``

Force HTTPS. There should be no reason to turn this off.

SOCIALHOME_LOG_DISABLE_ADMIN_EMAILS
...................................

Default: ``False``

Set this to ``True`` to disable the Django admin error emails in production.

.. _config-log-target:

SOCIALHOME_LOG_TARGET
.....................

Default: ``file``

Define target for Django and application logs. Possible options:

* ``file``, logs will go to a file defined in ``SOCIALHOME_LOGFILE``. Note, due to multiple processes logging to the same file, this file log is only really useful for tailing or if running different processes on separate containers or machines.
* ``syslog``, logs to syslog, to the ``local7`` facility.

SOCIALHOME_LOGFILE
..................

Default: ``/tmp/socialhome.log``

Where to write the main application log.

SOCIALHOME_NODE_LIST_URL
........................

Default: ``https://the-federation.info/socialhome``

URL to make signup link go to in the case that signups are closed.

SOCIALHOME_RELAY_ID
...................

Default: not set

Configure an optional relay instance endpoint to send outgoing content to,
for example ``https://relay.domain.tld/receive/public``.

For more info see `relay system <https://git.feneas.org/jaywink/social-relay>`_.

SOCIALHOME_RELAY_SCOPE
......................

Default: ``none``

Possible values ``all`` or ``none``. Defines at which level the defined relay is subscribed with.
Set to ``none`` to disable the relay incoming subscription.
For more info see `relay system <https://git.feneas.org/jaywink/social-relay>`_.

SOCIALHOME_ROOT_PROFILE
.......................

Default: ''

If this is set to a local username, that users profile will be shown when navigating to ``/`` as not logged in user. Logged in users will still see their own profile. Good for single user instances.

SOCIALHOME_SHOW_ADMINS
......................

Default: ``False``

If set to ``True``, allows showing the server admins to users and in server metadata. The settings used are ``DJANGO_ADMIN_NAME`` and ``DJANGO_ADMIN_MAIL``.

.. _configuration-statistics:

SOCIALHOME_SILKY
................

Default: ``False``

Set to ``True`` to enable the `Django-Silk <https://github.com/jazzband/django-silk>`_ debugging tool.
Information about requests will be available at ``/_silk/``.

SOCIALHOME_STATISTICS
.....................

Default: ``False``

Controls whether to expose some generic statistics about the node. This includes local user, content and reply counts. User counts include 30 day and 6 month active users.

SOCIALHOME_STREAMS_PRECACHE_SIZE
................................

Default: ``100``

Amount of items to keep in stream precaches, per user, per stream. Increasing this setting can radically increase Redis memory usage. If you have a lot of users, you might consider decreasing this setting.

Note the amount actually stored can temporarily go over the limit. Cache trimming is done as a daily job, not every time a new item needs to be added to the cache.

SOCIALHOME_STREAMS_PRECACHE_INACTIVE_DAYS
.........................................

Default: ``90``

Amount of days since user has logged in to be considered inactive for streams precaching. See notes about ``SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE``.

SOCIALHOME_STREAMS_PRECACHE_INACTIVE_SIZE
.........................................

Default: ``0``

Amount of items to keep in stream precaches, per user, per stream, for inactive and anonymous users. By default maintenance will always clear the cache for inactive and anonymous users daily. See notes about ``SOCIALHOME_STREAMS_PRECACHE_SIZE``.

SOCIALHOME_SYSLOG_FACILITY
..........................

Default: ``local7``

Define the logging facility for syslog, if ``SOCIALHOME_LOG_TARGET`` is set to ``syslog``.

SOCIALHOME_SYSLOG_LEVEL
.......................

Default: ``INFO``

Define the logging level of syslog logging, if ``SOCIALHOME_LOG_TARGET`` is set to ``syslog``. Possible options: ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``.

SOCIALHOME_TOS_JURISDICTION
...........................

Default: ``None``

Define what jurisdiction (country) should be printed on the terms of service document. If not given, jurisdiction will not be included in the terms of service documents.
