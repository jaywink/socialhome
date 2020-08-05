.. _installation-docker:

Docker
------

The Docker images are relatively new, but have had some real production testing.

Currently the main application of Socialhome is packaged as one image. Inside the
image there is a single Circusd process which runs:

1) gunicorn,
2) django daphne,
3) a channels worker and
4) X amount of RQ worker processes.

It's possible wewill extract various components into separate Docker images in
the future.

In addition to the main image, the following are needed:

* Redis
* PostgreSQL
* Nginx or similar to serve media and/or provide SSL

There is an example
`docker-compose.yml <https://git.feneas.org/socialhome/socialhome/tree/master/docker/prod>`_
that shows how things can be set up. Socialhome environment variables can be used
to point to an external Redis or PostgreSQL if need be. See :ref:`configuration`.

The image can be pulled using:

::

    docker pull registry.git.feneas.org/socialhome/socialhome


Find the Socialhome images in the
`Docker registry <https://git.feneas.org/socialhome/socialhome/container_registry>`_.

In order to configure your reverse-proxy if you don't use the example `docker-compose.yml`,
here are a few hints:

1) the Socialhome application run on port 5000 with HTTP protocol,
2) it exposes the `/robots.txt` and /favicon.ico files;
3) Django Daphne runs on port 23564 with Websockets protocol; you should redirect the `/ch/` route to `ws://127.0.0.1:23564/ch/`
