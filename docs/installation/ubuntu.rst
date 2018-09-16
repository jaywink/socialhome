.. _installation-ubuntu:

Ubuntu (14.04)
--------------

This guide is very opinionated and experienced sysadmins will most likely want to do things differently. This guide will give you a Socialhome production install on uWSGI using an Apache2 web server.

Supported versions
..................

This guide is written for **Ubuntu 14.04** (with Upstart). For a SystemD config file, see :ref:`installation-other-systemd`.

Steps
.....

Fix locales
'''''''''''

Ubuntu 14.04 has a problem with locales which could bring problems when installing PostgreSQL. If you have already installed PostgreSQL, you can probably skip this step.

Check these two commands:

::

    echo $LANGUAGE
    echo $LC_ALL

if both of them come out empty, edit the file ``/etc/default/locale`` and add the two following lines:

::

    LANGUAGE="en_US.UTF-8"
    LC_ALL="en_US.UTF-8"

Save, logout and log back in.

See `this post <https://www.digitalocean.com/community/questions/language-problem-on-ubuntu-14-04>`_ for example for a description of this problem.

Install system packages
'''''''''''''''''''''''

::

    # Generic packages needed
    sudo apt-get install git python-virtualenv python3-setuptools python-dev python3-dev build-essential

    # PostgreSQL dependencies
    sudo apt-get install libpq-dev

    # federation dependencies
    sudo apt-get install libxml2-dev libxslt-dev lib32z1-dev

    # Redis
    sudo apt-get install redis-server

Install Node.js
'''''''''''''''

Node.js version 6-8 has been tested to work. Install one by following the `Node.js install guides <https://nodejs.org/en/download/package-manager/#debian-and-ubuntu-based-linux-distributions>`_.

If you already have a system Node installed which is either too old or newer, consider using [NVM](https://github.com/creationix/nvm) to install a specific version for Socialhome only.

Install PostgreSQL
''''''''''''''''''

If not installed or not using a remote PostgreSQL DB, install the database engine.

::

    sudo apt-get install postgresql

Create a database and user. Note down password for later.

::

    sudo su - postgres
    createuser -P socialhome
    createdb -O socialhome socialhome
    exit

Create a local user
'''''''''''''''''''

It's better to run applications under their own user.

::

    sudo adduser socialhome --disabled-login
    sudo chmod 750 /home/socialhome

    # Add user group to www-data groups so we can protect users home folder
    sudo adduser www-data socialhome

Set up uWSGI
''''''''''''

::

    # Create logs path
    sudo -u socialhome mkdir /home/socialhome/logs

Create the ini file with ``/home/socialhome/uwsgi.ini`` and add the following contents to it.

::

    [uwsgi]
    chdir=/home/socialhome/socialhome
    module=config.wsgi:application
    master=True
    pidfile=/tmp/socialhome-master.pid
    vacuum=True
    max-requests=5000
    logto=/home/socialhome/logs/uwsgi-master.log
    virtualenv=/home/socialhome/.virtualenvs/socialhome
    processes=2
    threads=2
    enable-threads=True
    socket=127.0.0.1:31452/
    uid=socialhome
    gid=socialhome
    harakiri=30

Set up Apache
'''''''''''''

if not already installed, install the Apache2 web server.

::

    sudo apt-get install apache2 libapache2-mod-proxy-uwsgi

Enable some necessary modules.

::

    sudo a2enmod proxy_uwsgi
    sudo a2enmod proxy_wstunnel
    sudo a2enmod proxy
    sudo a2enmod ssl

Add an Apache virtualhost file ``/etc/apache2/sites-available/socialhome.conf`` with the following content, replacing instances of ``yourdomain.tld`` with your real domain for your Socialhome instance:

::

    <VirtualHost *:80>
        ServerName yourdomain.tld
        ServerAlias www.yourdomain.tld
        RedirectPermanent / https://yourdomain.tld/
    </VirtualHost>

    <VirtualHost *:443>
        ServerName yourdomain.tld
        ServerAlias www.yourdomain.tld
        ServerAdmin webmaster@yourdomain.tld

        Alias /robots.txt /home/socialhome/socialhome/staticfiles/robots.txt
        Alias /favicon.ico /home/socialhome/socialhome/staticfiles/favicon.ico
        Alias /media /home/socialhome/socialhome/socialhome/media

        <Directory /home/socialhome/socialhome/socialhome/media>
            Require all granted
            Options -MultiViews -Indexes
        </Directory>

        ProxyPass /media !
        ProxyPass /ch/ ws://127.0.0.1:23564/ch/
        ProxyPass / uwsgi://127.0.0.1:31452/

        SSLEngine on
        SSLCertificateFile /etc/letsencrypt/live/yourdomain.tld/cert.pem
        SSLCertificateKeyFile /etc/letsencrypt/live/yourdomain.tld/privkey.pem
        SSLCertificateChainFile /etc/letsencrypt/live/yourdomain.tld/chain.pem
    </VirtualHost>

Enable Apache virtualhost

::

    sudo a2ensite socialhome

Get LetsEncrypt certificate
'''''''''''''''''''''''''''

We wouldn't want to run our site without HTTPS. Install Certbot and get an LetsEncrypt certificate.

::

    sudo apt-get install software-properties-common
    sudo add-apt-repository ppa:certbot/certbot
    sudo apt-get update
    sudo apt-get install python-certbot-apache

Launch Certbot and answer any questions to install the certificates.

::

    certbot --apache certonly

Now you should be able to restart Apache.

::

    sudo service apache2 restart

Change to Socialhome user
'''''''''''''''''''''''''

.. include:: /includes/socialhome_user.rst

Install Virtualenvwrapper
'''''''''''''''''''''''''

This is the easiest way to manage Python virtualenvs. We also add production Django configuration reference at the same time.

::

    pip install --user virtualenvwrapper

Add the following lines to your ``.bashrc`` and reload it via ``source ~/.bashrc``.

::

    export WORKON_HOME=$HOME/.virtualenvs
    source ~/.local/bin/virtualenvwrapper.sh
    export DJANGO_SETTINGS_MODULE=config.settings.production

Create Python virtualenv
''''''''''''''''''''''''

Python 3.6+ is required! If your system Python 3 is not at least this version, please install Python 3.6 and replace ``/usr/bin/python3`` in the below command with the path to the Python 3.6 binary.

::

    mkvirtualenv -p /usr/bin/python3 socialhome

The virtualenv is automatically activated. When you need it in the future, just type ``workon socialhome``.

Update pip and setuptools
'''''''''''''''''''''''''

::

    pip install -U pip setuptools

Install pip-tools
'''''''''''''''''

``pip-tools`` is a handy tool to keep environments clean and all dependencies nicely pinned.

::

    pip install -U pip-tools

Get Socialhome code
'''''''''''''''''''

::

    git clone https://github.com/jaywink/socialhome
    cd socialhome

Install Python dependencies
'''''''''''''''''''''''''''

.. include:: /includes/python_dependencies.rst

Create configuration
''''''''''''''''''''

Create the file ``.env`` with the following contents, replacing values as needed.

You must change or add the following values:

* Replace ``DATABASEPASSWORDHERE`` with the database password typed in earlier.
* ``DJANGO_SECRET_KEY`` must be added. Generate one for example `here <http://www.miniwebtool.com/django-secret-key-generator/>`_.
* Place your domain in ``DJANGO_ALLOWED_HOSTS`` and ``SOCIALHOME_DOMAIN``.

::

    DATABASE_URL=postgres://socialhome:DATABASEPASSWORDHERE@127.0.0.1:5432/socialhome
    DJANGO_SECRET_KEY=
    DJANGO_ALLOWED_HOSTS=yourdomain.tld
    DJANGO_SECURE_SSL_REDIRECT=True
    DJANGO_ACCOUNT_ALLOW_REGISTRATION=True
    SOCIALHOME_DOMAIN=yourdomain.tld
    SOCIALHOME_HTTPS=True
    SOCIALHOME_LOGFILE=/home/socialhome/logs/socialhome.log

For further configuration tips, see :ref:`running`.

Make the env file a bit less readable.

::

    chmod 0600 .env

Configure email sending
'''''''''''''''''''''''

Note, email *is* required for signing up. Users will **not** be able to sign up if the instance does not have working email sending. See :ref:`email-config` on how to configure email sending.

Run migrations
''''''''''''''

.. include:: /includes/migrations.rst

Install statics
'''''''''''''''

.. include:: /includes/install_statics.rst

Search index
''''''''''''

.. include:: /includes/search_index.rst

Set the correct domain name in Django
'''''''''''''''''''''''''''''''''''''

Load up the Django shell with ``python manage.py shell_plus`` and then execute the following, replacing "yourdomain.tld" with your domain and "Socialhome" as the name of your site, assuming you want the name changed:

::

    Site.objects.filter(id=1).update(domain="yourdomain.tld", name="Socialhome")
    exit

Set up Circus
'''''''''''''

Exit Socialhome user and create Upstart configuration for Circus process manager. Circus is used to control various processes that are needed in addition to the web server. This allows starting one process that will start and maintain a bunch of other processes we need. A configuration file for the processes is provided within the repository.

Create Upstart configuration ``/etc/init/socialhome.conf`` with the following content:

::

    description "Socialhome"
    start on runlevel [2345]
    stop on runlevel [06]
    setuid socialhome
    setgid socialhome

    respawn

    env PYTHONPATH="/home/socialhome/socialhome"
    env SOCIALHOME_HOME="/home/socialhome"
    env RQWORKER_NUM=5
    env VIRTUAL_ENV=/home/socialhome/.virtualenvs/socialhome
    env LC_CTYPE=en_US.UTF-8
    env LC_ALL=C.UTF-8
    env LANG=C.UTF-8
    env DJANGO_SETTINGS_MODULE=config.settings.production

    chdir /home/socialhome/socialhome

    exec /home/socialhome/.virtualenvs/socialhome/bin/circusd config/circus.ini

Start Circus. It will automatically start on system boot.

::

    sudo service socialhome start

For a SystemD config file, see :ref:`installation-other-systemd`.

Done!
'''''

That wasn't so hard was it? Navigate to the domain you chose to install Socialhome on and hopefully you will see a landing page. Signups will be open.

Final tweaks
''''''''''''

Unless you want to keep signups open, after creating your own account, you should close the signups to avoid random people signing up to your instance. See configuration tips at :ref:`running`.

If you didn't configure emails, you cannot complete your user account registration without the email confirmation link. See :ref:`shell-email-confirm`.

If you want to set your initially created user as admin, see :ref:`admin-user`.

Terms of Service and Privacy policy documents are good to have. These tell people visiting your site what rules you operate with. Socialhome provides default templates you can activate with a few clicks. See :ref:`policy-docs` for more info.
