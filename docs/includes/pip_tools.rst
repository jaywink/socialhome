We use ``pip-tools`` as the way to install Python dependencies. All the "base" dependencies, including production deployment dependencies are locked in ``requirements.txt``. The file ``dev-requirements.txt`` includes both the base and the extra development/testing related dependencies.

To use ``pip-tools``, first install it:

::

    # Ensure pip and setuptools are up to date as well
    pip install -U pip pip-tools

Then install dependencies:

::

    # Production environment
    pip-sync

    # Development environment
    pip-sync dev-requirements.txt

It is not mandatory to use ``pip-tools`` for running a production installation. For development it is mandatory. All dependencies should be placed (unlocked) in either ``requirements/requirements.in`` (base) or ``requirements/requirements-dev.in`` (development extras). Then execute ``./compile-requirements.sh`` to update the locked dependency files after each change to the ``.in`` files. See `pip-tools <https://github.com/jazzband/pip-tools>`_ for more information.
