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

Python 3.6 is the minimum supported version. Ensure the following are installed:

* Python system dependencies
* NodeJS (version 6-8)
* PostgreSQL server
* Redis

The file ``requirements.apt`` contains other various dependencies. You can use the ``install_ubuntu_dependencies.sh`` script to help installing these.

You can use the ``install_alpine_dependencies.sh`` script to install required dependencies (including Python, NodeJS, PostgreSQL and Redis) on Alpine.

To generate profiling SVG's with pytest, also install the ``graphviz`` package (for example from apt), which provides ``dot``.

Install Python dependencies
...........................

.. include:: includes/pip_tools.rst

Do NPM, Bower
.............

::

    npm install
    bower install
    sudo npm -g install grunt
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

Running the Django shell
........................

It is recommended to use the enhanced "shell plus" provided by Django Extensions package which is automatically installed via the development dependencies. One of the benefits is that it will automatically import all project models.

To launch the shell:

::

    python manage.py shell_plus

Creating a user
...............

To create an *superuser account*, use this command:

::

    python manage.py createsuperuser

After this you need to log in once with the user via the user interface (which creates an email confirmation) and then run the following in the Django shell to confirm the email:

::

    from allauth.account.models import EmailAddress
    EmailAddress.objects.all().update(verified=True)

You should now be able to log in as the user ``admin``.

Search index
............

.. include:: includes/search_index.rst

Running tests
-------------

The user needs right to create databases:

::

    # On some distributions, regular users are not sudoers; you may need to type:
    #    su -
    su - postgres
    psql -c "ALTER USER socialhome CREATEDB;"

Python tests
............

::

    py.test

To also generate profiling information, add ``--profile --profile-svg`` to the command.

JavaScript tests
................

Execute the following to run the frontend JavaScript tests.

::

    npm run test

API Routes
-----------

There is a dependency in the API route URL configurations with the new Vue based frontend tests. If you change or add new API routes during development, you must also do the following:

::

    python manage.py collectstatic_js_reverse
    mv staticfiles/django_js_reverse/js/reverse.js socialhome/frontend/tests/fixtures/Url.js

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

Commit and author stats
.......................

Some commands to get nice stats for release posts.

**Authors**

::

    git shortlog -s -n -e <first release commit>..HEAD --no-merges

**Changes**

::

    git diff --stat <first release commit>..HEAD

Developing with Docker
------------------------

If you choose, you may develop Socialhome using Docker, rather than installing Postgres and Redis manually on your computer.


Supported versions
..................

This guide assumes you are running Docker on a GNU/Linux based system such as Ubuntu, Debian or Fedora Linux. It may be possible to run this on other platforms where Docker is supported, but those are untested.

The docker development installation was tested on Docker version 17.09 and docker-compose 1.16.1.

Steps
......

The first step is to copy the example docker-compose file ``docker/dev/docker-compose.yml.example`` file to the root of the project. eg

``cp docker/dev/docker-compose.yml.example ./docker-compose.yml``

You also need to set an .env file as per the above instructions. Use the ``.env.example`` as a starting point.

From there, you can build the images:

``docker-compose build``

And then the steps you would normally do, but throught he django image, ala:

``docker-compose run django manage migrate``
and
``docker-compose run django manage createsuperuser``

And then just

``docker-compose up``

Defaults
..........

The defaults are that that the Docker image will be running on port 8000 and then exposed to the host OS on the same port (ie you can browse to http;//localhost:8000 to see the Django instance running). Redis and Postgres will be running but not exposed to the host OS by default. These can be changed on the ``docker-compose.yml`` file.

Generating dummy content
------------------------

There is a management command to generate a bunch of dummy ``Content`` objects. Please feel free to expand it with more configuration options and different types of content. To use it, run the following:

::

    python manage.py create_dummy_content

``--help`` will give you available options.

Contact for help
----------------

See our communication channels in the :ref:`community` page.

You can also ask questions or give feedback via issues.
