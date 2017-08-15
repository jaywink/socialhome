.. _api:

API
===

Socialhome has a REST API. This allows to build clients, bots and alternative frontends.

Note, some parts of the API are still work in progress and thus changes could still happen.

API routes
----------

The API methods and data can be browsed using the endpoint ``/api/``. Shown endpoints and data depends on your user credentials (log-in using the menu if not already).

Authenticating
--------------

The API supports two authentication methods:

Session authentication
......................

This means when you are logged into Socialhome, you automatically have usage of the API from the browser. Note however that POST/PUT/PATCH methods will require CSRF tokens.

Token authentication
....................

API authentication can happen by setting the required HTTP header as follows:

::

    Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b

Your client can obtain a token for the user by posting ``username`` and ``password`` as form data or JSON to the view ``/api-token-auth/``. This will return a token as follows:

::

    { 'token' : '9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b' }

Users can also retrieve and regenerate tokens from the UI from their profile menu.

Development
-----------

The API is made with `Django REST Framework <http://www.django-rest-framework.org/>`_. Help is welcome to expand the API!

Clients
-------

See the :ref:`clients` section.
