.. _development:

Development
===========

Socialhome is missing features and needs a lot of polish on the UI side. If you are familiar with Django (or want to learn!) and are interested in getting involved, please don't hesitate to get in touch!

For guidelines how to contribute, please first read the :ref:`contributing` guide.

* `Source code repo <https://github.com/jaywink/socialhome>`_
* `Issue tracker <https://github.com/jaywink/socialhome/issues>`_
* `Kanban board <https://waffle.io/jaywink/socialhome>`_

Environment setup
-----------------

Instructions are for Ubuntu 16.04+ (+ simple Alpine 3.6 dependencies script). Please contribute via PR's if you notice anything missing or want to contribute instructions for another platform.

Python Virtualenv
.................

Python 3.4, 3.5 and 3.6 are officially tested against. Ensure the following are installed:

* Python system dependencies
* NodeJS (version 6+)
* PostgreSQL server
* Redis

The file ``requirements.apt`` contains other various dependencies. You can use the ``install_ubuntu_dependencies.sh`` script to help installing these.

You can use the ``install_alpine_dependencies.sh`` script to install required dependencies (including Python, NodeJS, PostgreSQL and Redis) on Alpine.

Install Python dependencies
...........................

.. include:: includes/pip_tools.rst

Do NPM, Bower
.............

::

    npm install
    bower install
    sudo npm -g install grunt
    grunt dev

New Vue based frontend
......................

The new Vue based frontend builds the bundles with Webpack. Execute the following to build the bundle.

::

    npm run dev

To watch files and build bundles automatically, use this.

::

    npm run watch

Configure
.........

Configuration is done via environment variables. For the meaning of them, look them up under files in ``config/settings``. Values in the file ``.env`` will be used automatically.

::

    cp .env.example .env

Edit any values necessary. By default the ``SECRET_KEY`` is empty. You MUST set something to it. We don't supply a default to force you to make it unique in your production app.

Create a database
.................

If you changed the ``DATABASE_URL`` in the settings file, make sure to change the values in these commands accordingly.

::

    sudo su - postgres
    createuser -s -P socialhome  # give password 'socialhome'
    createdb -O socialhome socialhome
    exit
    python manage.py migrate

Running the development server
..............................

Just use the standard command:

::

    python manage.py runserver

Unfortunately ``runserver_plus`` cannot be used as it does not integrate with Django Channels.

Creating a user
...............

To create an *superuser account*, use this command:

::

    python manage.py createsuperuser

After this you need to log in once with the user via the user interface (which creates an email confirmation) and then run the following in the Django shell to confirm the email:

::

    EmailAddress.objects.all().update(verified=True)

You should now be able to log in as the user ``admin``.

Search index
............

.. include:: includes/search_index.rst

Running tests
-------------

Python tests
............

::

    py.test

JavaScript tests
................

Legacy frontend
'''''''''''''''

This will launch a separate ``runserver`` on port 8181 and execute the tests against that. The separate ``runserver`` instance will be killed after the tests have been executed.

::

    grunt test

New Vue based frontend
''''''''''''''''''''''

Execute the following to run the new frontend JavaScript tests.

::

    npm run test

API routes
----------

There is a dependency in the API route URL configurations with the new Vue based frontend tests. If you change or add new API routes during development, you must also do the following:

::

    python manage.py collectstatic_js_reverse
    mv staticfiles/django_js_reverse/js/reverse.js socialhome/streams/app/tests/fixtures/Url.js

This updates the JavaScript fixtures with the new URL configuration.

Linters
-------

ESLint
......

There is an ``.eslintrc`` provided. We follow the Airbnb and Vue guidelines with some tweaks. It's recommended to add this configuration to your editor directly. To run ESLint directly, use the following command. NOTE! This is only valid for the new Vue based frontend, not JS in ``socialhome/static``.

::

    npm run lint

Building local documentation
----------------------------

::

    cd docs
    make html

Doing a release
---------------

Bump version number in three places:

* ``socialhome/__init__.py``
* ``docs/conf.py``
* ``docs/changelog.rst``

To generate a markdown version of the release changelog, first install ``Pandoc``:

::

    sudo apt install pandoc

Then execute the following and copy the markdown version for pasting to GitHub releases or a Socialhome post:

::

    pandoc --from rst --to markdown_github docs/changelog.rst | less

After the release commit has been pushed and a release has been tagged, set a development version in the same above files. This is basically the next minor release postfixed by ``-dev``.

Contact for help
----------------

See our communication channels in the :ref:`community` page.

You can also ask questions or give feedback via issues.
