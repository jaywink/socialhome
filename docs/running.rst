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
* Local settings in ``env.local`` (assuming you are using this way to configure the application)
* The path ``socialhome/media/`` which contains for example image uploads

Configuration
-------------

Configuration mainly happens through environment variables. Those are passed to Django via the file ``env.local`` in the repository root. The following items of note can be changed.

After making changes to this file, don't forget to reload the app with ``sudo service socialhome restart``.

DATABASE_URL
............

Default: ``postgres:///socialhome``

This must be set to a proper database URL, for example ``postgres://socialhome:DATABASEPASSWORDHERE@127.0.0.1:5432/socialhome``.

DJANGO_ACCOUNT_ALLOW_REGISTRATION
.................................

Default: ``true``

Set this to ``false`` if you want to disable signups.

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
* ``DJANGO_EMAIL_USE_TLS`` (default ``true``)
* ``DJANGO_EMAIL_USE_SSL`` (default ``false``)
* ``DJANGO_EMAIL_TIMEOUT`` (default '')
* ``DJANGO_EMAIL_SSL_KEYFILE`` (default '')
* ``DJANGO_EMAIL_SSL_CERTFILE`` (default '')
* ``DJANGO_EMAIL_SUBJECT_PREFIX`` (default ``[Socialhome]``)
* ``DJANGO_SERVER_EMAIL`` (default ``noreply@socialhome.local``)

Note, email *is* required for signing up. Users will **not** be able to sign up if the instance does not have working email sending.

DJANGO_OPBEAT_ENABLE
....................

Default: ``false``

If you wish to enable Opbeat integration, set this to ``true``. Also remember to set ``DJANGO_OPBEAT_ORGANIZATION_ID``, ``DJANGO_OPBEAT_APP_ID`` and ``DJANGO_OPBEAT_SECRET_TOKEN`` to the values from Opbeat.

DJANGO_SECRET_KEY
.................

Default: ''

Must be set to a long secret string. Don't expose it to anyone. See `docs <https://docs.djangoproject.com/en/dev/ref/settings/#secret-key>`_

DJANGO_SECURE_CONTENT_TYPE_NOSNIFF
..................................

Default: ``true``

See `docs <https://django-secure.readthedocs.io/en/latest/settings.html#secure-content-type-nosniff>`_.

DJANGO_SECURE_FRAME_DENY
........................

Default: ``true``

See `docs <https://django-secure.readthedocs.io/en/latest/settings.html#secure-frame-deny>`_.

DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS
.....................................

Default: ``true``

See `docs <https://docs.djangoproject.com/en/1.11/ref/settings/#secure-hsts-include-subdomains>`_.

DJANGO_SECURE_SSL_REDIRECT
..........................

Default: ``true``

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

SOCIALHOME_DOMAIN
.................

Default: ``socialhome.local``

Must be set to your Socialhome instance domain. Used for example to generate outbound links.

SOCIALHOME_HTTPS
................

Default: ``true``

Force HTTPS. There should be no reason to turn this off.

SOCIALHOME_LOGFILE
..................

Default: ``/tmp/socialhome.log``

Where to write the main application log.

SOCIALHOME_LOGFILE_FEDERATION
.............................

Default: ``/tmp/socialhome-federation.log``

Where to write the federation layer log.

SOCIALHOME_RELAY_DOMAIN
.......................

Default: ``relay.iliketoast.net``

Which relay instance to send outgoing content to. Socialhome automatically integrates with the `relay system <https://github.com/jaywink/social-relay>`_.

SOCIALHOME_ROOT_PROFILE
.......................

Default: ''

If this is set to a local username, that users profile will be shown when navigating to ``/`` as not logged in user. Logged in users will still see their own profile. Good for single user instances.

