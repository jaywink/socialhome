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
