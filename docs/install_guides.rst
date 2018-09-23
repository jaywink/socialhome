.. _install-guides:

Install guides
==============

These instructions are for a production installation. For development installation instructions, see the :ref:`development` pages.

If you have issues following these instructions, please contact us via :ref:`community`.

Available guides:

* :ref:`installation-ubuntu`
* :ref:`installation-ubuntu-ansible`
* :ref:`installation-other-systemd`

.. include:: installation/ubuntu.rst

.. _installation-ubuntu-ansible:

Ubuntu (14.04, Ansible)
-----------------------

See this `Ansible role <https://git.feneas.org/socialhome/ansible-socialhome>`_.

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
