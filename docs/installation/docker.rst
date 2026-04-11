.. _installation-docker:

Docker
------

This page explains how to setup the Socialhome using Docker.

If you have issues following the supported instructions, please contact us via :ref:`community`.

The backend application
.......................

The main application container has the following process controlled by the main Circus process:

* Daphne for http and websocket traffic
* The configured number of RQ workers
* An RQ scheduler

The backend application container does not serve media and does not include any frontend.

The backend containers can be found at https://codeberg.org/socialhome/-/packages/container/socialhome

The frontend application
........................

Currently there are no Docker images for the frontend application. You will need to serve
the extracted frontend files via your chosen web server.

The frontend packages can be found at https://codeberg.org/socialhome/-/packages/generic/socialhome-ui

Backend memory requirements
'''''''''''''''''''''''''''

On average the container will require approximately 360mb of RAM plus approx 75mb per RQ
worker. The default RQ worker count is 1 though on a busy instance you may need many more. The
amount of RQ workers can be controlled with the environment variable ``RQWORKER_NUM``. The default
daphne worker count is also 1 and can be controlled with the ``DAPHNE_WORKER_NUM`` environment
variable.

Routing to the backend
''''''''''''''''''''''

The following path prefixes need to be routed to port **23564** on the backend container:

* ``/ch``
* ``/receive``
* ``/admin``
* ``/api``
* ``/django-rq``
* ``/fetch``
* ``/hcard``
* ``/jsi18n``
* ``/nodeinfo``
* ``/static``
* ``/webfinger``
* ``/.well-know``

Additionally, the following header regexes should be routed to the backend container container
port **23564** as well:

* ``Accept: .*application/((activity|ld)\\+)?json.*``
* ``Accept: .*application/(xrd\\+|magic-envelope\\+)xml.*``

It should be safe to default anything not going to the backend to look for a frontend
package file. See `here <https://codeberg.org/socialhome/socialhome-ui/src/branch/main/INSTALLATION.md#versions-0-9-0-backend-0-22>`_
for an example NGINX config file.

TLS should be terminated by a load balancer before sending traffic to the application container.

The load balancer should also set the following headers:

* ``X-Forwarded-Proto: https``

Routing to the frontend
'''''''''''''''''''''''

The following path prefixes and files should serve the frontend:

* ``index.html``
* ``favicon.ico``
* ``/assets``

It should be safe to default anything not going to the backend to look for a frontend
package file. See `here <https://codeberg.org/socialhome/socialhome-ui/src/branch/main/INSTALLATION.md#versions-0-9-0-backend-0-22>`_
for an example NGINX config file.

Backend container volumes
'''''''''''''''''''''''''

Two paths should be mounted on the host and persisted over recreation of the container:

* ``/app/socialhome/media`` as read write. The app will write uploaded media to this path.
* ``/app/var`` as read write. The app will maintain things like search indexes here.

Backend configuration
'''''''''''''''''''''

Socialhome uses environment variables for configuration. At minimum, you need to modify the following:

* ``DATABASE_URL`` (PostgreSQL connection URI)
* ``DJANGO_SECRET_KEY`` a random secret key for sessions etc - make this long and
  do NOT change this after setup.
* ``DJANGO_ALLOWED_HOSTS`` your Socialhome domain
* ``SOCIALHOME_DOMAIN`` your Socialhome domain
* ``REDIS_HOST`` hostname of your Redis instance
* ``RQWORKER_NUM`` the amount of RQ worker processes you want to run (default 1)
* ``DAPHNE_WORKER_NUM`` the amount of daphne processes you want to run (default 1)
* ``DJANGO_ACCOUNT_ALLOW_REGISTRATION`` either "True" or "False" depending whether you
  want to allow signups.

For more configuration values see :ref:`configuration`.

Other services
..............

PostgreSQL and Redis are set up as normal to their documentation. We recommend the latest
versions of both, they can either run as containers or on the network. Both the PostgreSQL
and the Redis data paths should be persisted over container recreation, if running
in containers.

The load balancer needs to take the following roles:

* termination of TLS
* serving the media

Media serving
'''''''''''''

Whatever load balancer is used, ensure to route ``/media`` path prefix to it. The load balancer
must handle TLS for this and deny indexing of the files. The files found under this
path should be the same ones mounted as read write to the application container.
