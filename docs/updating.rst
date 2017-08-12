.. _updating:

Updating
========

There are certain steps that should always be done when updating your node to new code. This will be a generic list of what to do when updating which should be near enough the same whatever way the app is installed. Commands might vary depending on your OS below.

If using the :ref:`installation-ubuntu-ansible` there is no need to do anything special. Just re-run the role!

Check the changelog
-------------------

When updating the code, make sure you check the :ref:`changelog` for any notes about the changes. Sometimes extra manual steps might be required or an update could take a long time due to database migrations.

Change to Socialhome user
-------------------------

.. include:: /includes/socialhome_user.rst

Activate virtualenv
-------------------

::

    workon socialhome

Pull in latest code or release
------------------------------

To pull in a release:

::

    # Replace release tag with the release, for example "v0.3.1"
    git fetch && git checkout <release tag>

To pull in master branch head:

::

    git pull


Install Python dependencies
---------------------------

.. include:: /includes/python_dependencies.rst

Run migrations
--------------

.. include:: /includes/migrations.rst

Install statics
---------------

.. include:: /includes/install_statics.rst

Restart the app
---------------

::

    sudo service socialhome restart

Done!
-----

Check the application and have fun!
