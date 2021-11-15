We use the ``pip-tools`` command to ensure dependencies are at the correct versions.

Ensure ``pip-tools`` are up to date:

::

    # Ensure pip and setuptools are up to date as well
    pip install -U pip pip-tools


Then, update dependencies:

::

    pip-sync
