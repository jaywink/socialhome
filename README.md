[![Build Status](https://travis-ci.org/jaywink/socialhome.svg?branch=master)](https://travis-ci.org/jaywink/socialhome) [![Stories in Ready](https://badge.waffle.io/jaywink/socialhome.png?label=ready&title=Ready)](https://waffle.io/jaywink/socialhome) [![Requirements Status](https://requires.io/github/jaywink/socialhome/requirements.svg?branch=master)](https://requires.io/github/jaywink/socialhome/requirements/?branch=master) [![codecov](https://codecov.io/gh/jaywink/socialhome/branch/master/graph/badge.svg)](https://codecov.io/gh/jaywink/socialhome) [![Code Health](https://landscape.io/github/jaywink/socialhome/master/landscape.svg?style=flat)](https://landscape.io/github/jaywink/socialhome/master)

# Socialhome

A federated social home. Provides home page functionality and federates with other federated social networks using the Diaspora protocol.

See an example site: https://jasonrobinson.me

## Status

Alpha. Only limited functionality. Here be dragons.

## FAQ

### Are there any public servers?

Currently no, since the software is very alpha. Plan is to set up a public demo server soon.

### How do I deploy it, can I just copy the files to a web server?

Unfortunately Socialhome is a bit more complex than that, being a Django project. You need to know the following at least:
* Linux administration
* Django deployment (via uWSGI, for example)
* Web server configuration

There is [an ansible role](https://github.com/jaywink/ansible-socialhome), if you are familiar with Ansible. But until something packaged is available like a Docker image, Socialhome will not be easy to deploy since it is a Django application that requires a full virtual server with root etc and system administration knowledge.

Running a development server however is easy. Just set up your virtualenv and create a settings file as below. Then use the built-in Django runserver command as usual.

## Development

### Installation

Create a virtualenv and activate it. Ensure the following are installed:

* Python system dependencies
* NodeJS
* PostgreSQL server
* Redis

Install requirements:

    pip install -r requirements/local.txt
    pip install -r requirements/test.txt
    
Do NPM, Bower

    npm install
    bower install
    sudo npm -g install grunt
    grunt dev
    
Create a database

    sudo su - postgres
    createuser -s -P socialhome  # give password 'socialhome'
    createdb -O socialhome socialhome
    exit
    python manage.py migrate
    
## Settings

See: http://cookiecutter-django.readthedocs.org/en/latest/settings.html

A basic env file is provided, see `env.example`. Copy this to `env.local` and fill with correct values. When running `manage.py` commands, these environment variables will be automatically loaded. For other usage (like `py.test`), load the environment in your shell with:

    export `cat env.local`

### Setting Up Your Users

To create a *normal user account*, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

To create an *superuser account*, use this command::

    python manage.py createsuperuser

### Running tests

Export your settings to the shell and then:

    py.test

## Celery

This app comes with Celery.

To run a celery worker:

    cd socialhome
    celery -A socialhome.taskapp worker -l info

Please note: For Celery's import magic to work, it is important *where* the celery commands are run. If you are in the same folder with *manage.py*, you should be right.

## Daphne/Websocket workers

In addition to the web server HTTP traffic and the Celery workers, Socialhome uses the Daphne server and Django Channels workers to handle websocket traffic. In development environments you don't need to worry about this - runserver will handle these for you. In production, check Django Channels documentation or the [Ansible role](https://github.com/jaywink/ansible-socialhome) on examples about running Daphne and the workers, and how to expose Daphne via Apache/NGINX for example.

## License

MIT
