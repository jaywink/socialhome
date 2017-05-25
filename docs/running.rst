.. _running:

Running an instance
===================

Some notes on running a production instance.

Django admin
------------

The normal Django admin can be found at ``/admin``.

Domain name
-----------

There is a dependency to ``contrib.sites`` which is used by ``django-allauth``. Thus, proper site domain name should be set in the ``Site`` table. This will appear for example in emails. By default the domain name is set to ``socialhome.network``.

Site name can be set in the Django admin or in shell as follows:

::

    Site.objects.filter(id=1).update(domain=<yourdomain>, name=<verbose name>)

Admin user
----------

If you used registration to create your first user instead of the Django ``createsuperuser`` command, log in to the shell and execute the following to set your user as superuser:

::

    User.objects.filter(username=<username>).update(is_staff=True, is_superuser=True)

Circus
------

To run background jobs in production, you can use or copy the provided Circus configuration. Note, running this is only necessary in production mode when deploying to a server.

If you have not installed the ``requirements/production.txt`` requirements, install Circus as follows:

::

    pip install circus

Run Circus as follows, replacing the number of background task workers if necessary:

::

    RQWORKER_NUM=5 circusd config/circus.ini

You can daemonize circus by passing an extra ``--daemonize`` flag.

Daphne/Websocket workers
------------------------

In addition to the web server HTTP traffic and the Celery workers, Socialhome uses the Daphne server and Django Channels workers to handle websocket traffic. In development environments you don't need to worry about this - runserver will handle these for you. In production, check Django Channels documentation or the `Ansible role <https://github.com/jaywink/ansible-socialhome>`_ on examples about running Daphne and the workers, and how to expose Daphne via Apache/NGINX for example.
