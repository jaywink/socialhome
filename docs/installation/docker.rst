.. _installation-docker:

Docker
------

The Docker images are relatively new, but have had some real production testing.

Currently the main application of Socialhome is packaged as one image. Inside the
image there is a single Circusd process which runs 1) gunicorn, 2) django daphne,
3) a channels worker and 4) X amount of RQ worker processes. It's possible we
will extract various components into separate Docker images in the future.

In addition to the main image, the following are needed:

* Redis
* PostgreSQL
* Nginx or similar to serve media and/or provide SSL

There is an example
`docker-compose.yml <https://gitlab.com/jaywink/socialhome/-/tree/master/docker/prod>`_
that shows how things can be set up. Socialhome environment variables can be used
to point to an external Redis or PostgreSQL if need be. See :ref:`configuration`.

Find the Socialhome images in the
`Docker registry <https://gitlab.com/jaywink/socialhome/container_registry>`_.
