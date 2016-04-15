[![Stories in Ready](https://badge.waffle.io/jaywink/socialhome.png?label=ready&title=Ready)](https://waffle.io/jaywink/socialhome)
# Socialhome

A federated social home.

## Status

Alpha. Only limited functionality. Here be dragons.

## Settings

See: http://cookiecutter-django.readthedocs.org/en/latest/settings.html

A basic env file is provided, see `env.example`. Copy this to `env.local` and fill with correct values. When running `manage.py` commands, these environment variables will be automatically loaded. For other usage (like `py.test`), load the environment in your shell with:

    export `cat env.local`

## Basic Commands

### Setting Up Your Users

To create a *normal user account*, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

To create an *superuser account*, use this command::

    python manage.py createsuperuser

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report::

    coverage run manage.py test
    coverage html
    open htmlcov/index.html

### Running tests with py.test

    py.test

### Live reloading and Sass CSS compilation

See: http://cookiecutter-django.readthedocs.org/en/latest/live-reloading-and-sass-compilation.html

## Celery

This app comes with Celery.

To run a celery worker:

    cd socialhome
    celery -A socialhome.taskapp worker -l info

Please note: For Celery's import magic to work, it is important *where* the celery commands are run. If you are in the same folder with *manage.py*, you should be right.

## License

MIT
