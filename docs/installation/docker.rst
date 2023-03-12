.. _installation-docker:

Docker
------

This page explains how to setup a Socialhome instance using Docker. While the core
of Socialhome is in one single container, the setup is a bit more complex due to other
services required. These can either be other containers, running on the host or other
machines.

If you have issues following the supported instructions, please contact us via :ref:`community`.

The application
...............

The main application container has the following process controlled by the main Circus process:

* Daphne for http and websocket traffic
* The configured number of RQ workers
* An RQ scheduler

The application container does not serve media.

Docker images
'''''''''''''

The containers can be found at the `GitLab docker registry <https://gitlab.com/jaywink/socialhome/container_registry>`_.

Each version will have a tag and additionally the ``latest`` tag contains the latest version.

Memory requirements
'''''''''''''''''''

On average the container will require approximately 360mb of RAM plus approx 75mb per RQ
worker. The default RQ worker count is 1 though on a busy instance you may need many more. The
amount of RQ workers can be controlled with the environment variable ``RQWORKER_NUM``. The default
daphne worker count is also 1 and can be controlled with the ``DAPHNE_WORKER_NUM`` environment
variable.

Networking
''''''''''

The following routing needs to be done:

* Everything to port **23564**

TLS should be terminated by a load balancer before sending traffic to the application container.

The load balancer should also set the following headers:

* ``X-Forwarded-Proto: https``

Volumes
'''''''

Two paths should be mounted on the host and persisted over recreation of the container:

* ``/app/socialhome/media`` as read write. The app will write uploaded media to this path.
* ``/app/var`` as read write. The app will maintain things like search indexes here.

Configuration
'''''''''''''

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
