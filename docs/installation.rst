.. _installation:

Installation
==============

System requirements
-------------------

Socialhome requires a Linux server with root access. It is not possible to install Socialhome on a shared server.

Resources
.........

Socialhome isn't particularly heavy, though obviously that depends on the amount of users and connections to
remote nodes. In default set up, Socialhome will be running the following:

* uWSGI (~200mb)
* Daphne (~60mb)
* Circus (~25mb)
* 5x RQ workers (~75mb each == 375mb)
* RQ scheduler (~75mb)

Memory values are taken from a running production instance. This gives a total of 735mb of RAM used by the application.
Additionally, you need to allocate for PostgreSQL and Redis. A few gigabytes of available memory should easily be
enough to run a node with medium activity.

Disk space will mostly be required for content and image uploads. As an example of database size, 100K content
objects takes approx 230mb in the database. Image upload disk requirements depends entirely on the sizes of the uploads.

Install guides
--------------

These instructions are for a production installation. For development installation instructions, see the :ref:`development` pages.

If you have issues following these instructions, please contact us via :ref:`community`.

The recommended installation method is using the official
`Docker images <https://git.feneas.org/socialhome/socialhome/container_registry>`_. Other guides
will possibly be out of date and will likely be removed from the official documentation
at some point.

Available guides:

* :ref:`installation-docker`
* :ref:`installation-ubuntu-ansible`
* :ref:`installation-ubuntu`
* :ref:`installation-other-systemd`

.. include:: installation/docker.rst

.. _installation-ubuntu-ansible:

Ubuntu via Ansible
------------------

See this `Ansible role <https://git.feneas.org/socialhome/ansible-socialhome>`_.

.. include:: installation/ubuntu.rst

.. _installation-other-systemd:

Other Linuxes or newer Ubuntu using SystemD
------------------------------------------------

Follow the Ubuntu 14.04 guide, tweaking it to your system. For SystemD, try the following service config (for example saved to ``/etc/systemd/system/socialhome.service``):

::

    [Unit]
    Description=Socialhome Django script
    After=syslog.target network.target

    [Service]
    Environment=DJANGO_SETTINGS_MODULE="config.settings.production"
    Environment=PYTHONPATH="/home/socialhome/socialhome"
    Environment=SOCIALHOME_HOME="/home/socialhome"
    Environment=RQWORKER_NUM=5
    Environment=VIRTUAL_ENV=/home/socialhome/.virtualenvs/socialhome

    User=socialhome
    Group=socialhome

    WorkingDirectory=/home/socialhome/socialhome
    ExecStart=/home/socialhome/.virtualenvs/socialhome/bin/circusd /home/socialhome/socialhome/config/circus.ini
    Restart=always

    [Install]
    WantedBy=multi-user.target

Other platforms
---------------

PR's welcome for guides for more platforms!
