.. _faq:

FAQ
===

Generic questions regarding Socialhome.

If I run an instance, will it automatically connect to the network?
-------------------------------------------------------------------

No, Socialhome doesn't work in a peer2peer sense. Incoming content does not happen automatically, outbound does in a limited sense. Federation happens on two main principles:

* Social relationships

  This means content you create will be sent to the servers that your followers are on. Content that users you follow will send content they create to your server. The more inter-server relationships users on the server you are on, the more content will reach your server. This is the standard federation model in use by the Diaspora, OStatus and ActivityPub powered networks.

* The public content relay system

  The relay system is a network of servers that exist for one single purpose, to receive public content and to distribute it to places it would not otherwise reach (with social relationships based federation). Socialhome by default integrates with the relay system by sending all public content to it and subscribing to all public content on the relays. To receive content, this requires registering the Socialhome server to the relays so that they know about the server and can start sending content.

  Registration happens at `The-Federation.info <https://the-federation.info>`_. For more technical details about the relay system, check the `reference server documentation <https://git.feneas.org/jaywink/social-relay/blob/master/docs/relays.md>`_.

As a recap:

* To receive content from around the network, a new server can do the following:

  * Following other users on other servers to create social relationships. This happens by using the full handle (for example ``hq@socialhome.network``) of the user.
  * Registering to the relay system.

* To send out content to the network, a new server can do the following:

  * Following other users on other servers to create social relationships. Public content will also be sent out to the servers whose users *you* follow, not just who follow you.
  * No need to register with the relay. All public content created on a Socialhome server is by default sent out to the relay system.

.. _reporting-security-issues:

Welp I found a security issue, shall I just file an issue?
----------------------------------------------------------

No, please report security issues directly to the maintainers in private messages. Reporting security issues publicly in the issue tracker would allow other people to use the security issue to their benefit before a fix is released. Reporting security issues to the maintainers in private allows us to fix the issue and roll out a fix hopefully before many users are affected.

Please report security issues directly to the maintainer by email at ``mail@jasonrobinson.me``.

As admin, how do I delete a local user or block a remote spambot?
-----------------------------------------------------------------

Please see :ref:`delete-user-or-profile` section for instructions.

I accidentally shared someones content and it's stuck on my profile stream!
---------------------------------------------------------------------------

This is a `known issue with stream caching <https://gitlab.com/jaywink/socialhome/-/issues/567>`_.
Until it is fixed, ask your instance admin to manually clear your profile cache. It can be done with
the following command, on the machine where Redis is running.

::

    redis-cli --scan --pattern 'sh:streams:profile_all:<profile.id>:*' | xargs redis-cli del

Where ``<profile.id>`` should be replaced by the profile ID found via the Socialhome admin view.
