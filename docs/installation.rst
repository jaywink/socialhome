.. _installation:

Installation
============

System requirements
-------------------

Socialhome requires a Linux server with root access. It is not possible to install Socialhome on a shared server.

Resources
.........

Socialhome isn't particularly heavy, though obviously that depends on the amount of users and connections to remote nodes. In default set up, Socialhome will be running the following:

* uWSGI (~200mb)
* Channels worker (~85mb)
* Daphne (~60mb)
* Circus (~25mb)
* 5x RQ workers (~75mb each == 375mb)

Memory values are taken from a running production instance. This gives a total of 745mb of RAM used by the application. Additionally, you need to allocate for PostgreSQL and Redis. A few gigabytes of available memory should easily be enough to run a node with medium activity.

Disk space will mostly be required for content and image uploads. As an example of database size, 100K content objects takes approx 230mb in the database. Image upload disk requirements depends entirely on the sizes of the uploads.

Guides
------

See :ref:`install-guides`.
