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

    EmailAddress.objects.filter(email=<email>).update(verified=True)

This will allow the user to log in without clicking the confirmation email link.

.. _admin-user:

Admin user
----------

To make a user an admin, log in to the shell and execute the following to set the user as superuser:

::

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

Admin email for example for outgoing emails and providing a feedback channel for users.

DJANGO_ADMIN_NAME
.................

Default: ``Socialhome Admin``

Admin display name for example for outgoing emails.

DJANGO_ALLOWED_HOSTS
....................

Default: ``socialhome.local``

Domain that is used for this instance. Must be set to the right domain. Note, it's not a good idea to use a sub-domain wildcard for www, ie ``.`` as per Django docs. Federated sites work better with only one absolute domain.

DJANGO_DEFAULT_FROM_EMAIL
.........................

Default: ``noreply@socialhome.local``

Set this to the email address that emails should be sent out as.

.. _email-config:

DJANGO_EMAIL_BACKEND
....................

Default: ``django.core.mail.backends.console.EmailBackend``

Must be set to some real email backend if you wish to send emails. See `docs <https://docs.djangoproject.com/en/1.11/ref/settings/#email-backend>`_ for backend options and additional configuration help.

The possible email related additional settings are as follows:

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
* ``DJANGO_SERVER_EMAIL`` (default ``noreply@socialhome.local``)

Note, email *is* required for signing up. Users will **not** be able to sign up if the instance does not have working email sending.

DJANGO_OPBEAT_ENABLE
....................

Default: ``False``

If you wish to enable Opbeat integration, set this to ``True``. Also remember to set ``DJANGO_OPBEAT_ORGANIZATION_ID``, ``DJANGO_OPBEAT_APP_ID`` and ``DJANGO_OPBEAT_SECRET_TOKEN`` to the values from Opbeat.

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

SOCIALHOME_RELAY_DOMAIN
.......................

Default: ``relay.iliketoast.net``

Which relay instance to send outgoing content to. Socialhome automatically integrates with the `relay system <https://github.com/jaywink/social-relay>`_.

SOCIALHOME_ROOT_PROFILE
.......................

Default: ''

If this is set to a local username, that users profile will be shown when navigating to ``/`` as not logged in user. Logged in users will still see their own profile. Good for single user instances.

.. _configuration-statistics:

SOCIALHOME_STATISTICS
.....................

Default: ``False``

Controls whether to expose some generic statistics about the node. This includes local user, content and reply counts. User counts include 30 day and 6 month active users.

SOCIALHOME_STREAMS_PRECACHE_SIZE
................................

Default: ``100``

Amount of items to store in stream precaches, per user, per stream. Increasing this setting can radically increase Redis memory usage. If you have a lot of users, you might consider decreasing this setting. See :ref:`precaching`.

SOCIALHOME_SYSLOG_FACILITY
..........................

Default: ``local7``

Define the logging facility for syslog, if ``SOCIALHOME_LOG_TARGET`` is set to ``syslog``.

SOCIALHOME_SYSLOG_LEVEL
.......................

Default: ``INFO``

Define the logging level of syslog logging, if ``SOCIALHOME_LOG_TARGET`` is set to ``syslog``. Possible options: ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``.
