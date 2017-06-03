API
===

Socialhome has a (work in progress) REST API. This allows (in the future) to build clients, bots and alternative frontends.

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

Development
-----------

The API is made with `Django REST Framework <http://www.django-rest-framework.org/>`_. The idea is to have a full API that enables users to do everything that possibly could be required from a client or frontend UI. Help is welcome to expand the API!
