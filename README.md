[![Build Status](https://travis-ci.org/jaywink/socialhome.svg?branch=master)](https://travis-ci.org/jaywink/socialhome) [![Stories in Ready](https://badge.waffle.io/jaywink/socialhome.png?label=ready&title=Ready)](https://waffle.io/jaywink/socialhome) [![Dependency Status](https://gemnasium.com/badges/github.com/jaywink/socialhome.svg)](https://gemnasium.com/github.com/jaywink/socialhome) [![codecov](https://codecov.io/gh/jaywink/socialhome/branch/master/graph/badge.svg)](https://codecov.io/gh/jaywink/socialhome) [![Code Health](https://landscape.io/github/jaywink/socialhome/master/landscape.svg?style=flat)](https://landscape.io/github/jaywink/socialhome/master) [![](https://img.shields.io/badge/license-AGPLv3-red.svg)](https://tldrlegal.com/license/gnu-affero-general-public-license-v3-(agpl-3.0))

# Socialhome

A federated social home. Provides home page functionality and federates with other federated social networks using the Diaspora protocol.

Official demo site: https://socialhome.network

## Status

Alpha. Only limited functionality. Here be dragons.

## FAQ

### Are there any public servers?

Yes, the official demo site is at https://socialhome.network. Feel free to play around, however note that the software is still in early stages and even though attempts will be made to keep the data while doing development, no guarantees can be made.

### How do I deploy it, can I just copy the files to a web server?

Unfortunately Socialhome is a bit more complex than that, being a Django project. You need to know the following at least:
* Linux administration
* Django deployment (via uWSGI, for example)
* Web server configuration

There is [an ansible role](https://github.com/jaywink/ansible-socialhome), if you are familiar with Ansible. But until something packaged is available like a Docker image, Socialhome will not be easy to deploy since it is a Django application that requires a full virtual server with root etc and system administration knowledge.

Running a development server however is easy. Just set up your virtualenv and create a settings file as below. Then use the built-in Django runserver command as usual.

## Development

### Installation

#### Create a virtualenv and activate it

Python 3.4, 3.5 and 3.6 are officially tested against. Ensure the following are installed:

* Python system dependencies
* NodeJS
* PostgreSQL server
* Redis

The file `requirements.apt` contains other various dependencies. You can use the `install_os_dependencies.sh` script to help installing these.

#### Install requirements:

    pip install -r requirements/local.txt
    pip install -r requirements/test.txt
    
#### Do NPM, Bower

    npm install
    bower install
    sudo npm -g install grunt
    grunt dev
    
#### Configure

Configuration is done via environment variables. For the meaning of them, look them up under files in `config/settings`. Values in `env.local` will be used automatically.

    cp env.example env.local
    
Edit any values necessary. By default the `SECRET_KEY` is empty. You MUST set something to it. We don't supply a default to force you to make it unique in your production app.
    
#### Create a database

If you changed the `DATABASE_URL` in the settings file, make sure to change the values in these commands accordingly. 

    sudo su - postgres
    createuser -s -P socialhome  # give password 'socialhome'
    createdb -O socialhome socialhome
    exit
    python manage.py migrate
    
### Running the development server

Just use the standard command:

    python manage.py runserver
    
Unfortunately `runserver_plus` cannot be used as it does not integrate with Django Channels.
    
### Creating a user

To create an *superuser account*, use this command:

    python manage.py createsuperuser

After this you need to log in once with the user via the user interface (which creates an email confirmation) and then run the following in the Django shell to confirm the email:

    EmailAddress.objects.all().update(verified=True)
    
You should now be able to log in as the user `admin`.

### Running tests

#### Python tests

    py.test
    
#### JavaScript tests

This will launch a separate `runserver` on port 8181 and execute the tests against that. The separate `runserver` instance will be killed after the tests have been executed.

    grunt test

## Deployment

Some notes on deploying in production mode. A better guide will come later. 

### Django admin

The normal Django admin can be found at `/admin`.

### Domain name

There is a dependency to `contrib.sites` which is used by `django-allauth`. Thus, proper site domain name should be set in the `Site` table. This will appear for example in emails. By default the domain name is set to `socialhome.network`.

Site name can be set in the Django admin or in shell as follows:

    Site.objects.filter(id=1).update(domain=<yourdomain>, name=<verbose name>)
    
### Admin user

If you used registration to create your first user instead of the Django `createsuperuser` command, log in to the shell and execute the following to set your user as superuser:

    User.objects.filter(username=<username>).update(is_staff=True, is_superuser=True)

### Circus

To run background jobs in production, you can use or copy the provided Circus configuration. Note, running this is only necessary in production mode when deploying to a server.

If you have not installed the `requirements/production.txt` requirements, install Circus as follows:

    pip install circus
    
Run Circus as follows, replacing the number of background task workers if necessary:

    RQWORKER_NUM=5 circusd config/circus.ini
    
You can daemonize circus by passing an extra `--daemonize` flag.

### Daphne/Websocket workers

In addition to the web server HTTP traffic and the Celery workers, Socialhome uses the Daphne server and Django Channels workers to handle websocket traffic. In development environments you don't need to worry about this - runserver will handle these for you. In production, check Django Channels documentation or the [Ansible role](https://github.com/jaywink/ansible-socialhome) on examples about running Daphne and the workers, and how to expose Daphne via Apache/NGINX for example.

## License

Except where otherwise noted the code is licensed as [AGPLv3](https://tldrlegal.com/license/gnu-affero-general-public-license-v3-(agpl-3.0)).

Early work at and before commit [c36197491e996a599bd360e2b06853bbcb121c7a](https://github.com/jaywink/socialhome/commit/c36197491e996a599bd360e2b06853bbcb121c7a) was licensed as MIT.
