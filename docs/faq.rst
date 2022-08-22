.. _faq:

FAQ
===

Generic questions regarding Socialhome.

If I run an instance, will it automatically connect to the network?
-------------------------------------------------------------------

No, Socialhome doesn't work in a peer2peer sense. Federation happens via social relationshipts.

This means content you create will be sent to the servers that your followers are on.
Content that users you follow will send content they create to your server.
The more inter-server relationships users on the server you are on, the more content will
reach your server. This is the standard federation model in use by the ActivityPub and Diaspora
powered networks.

As a recap:

* To receive content from around the network, a new server should follow other users on
  other servers to create social relationships. This happens by using the full handle
  (for example ``hq@socialhome.network``) or federation ID (for example ``https://server.tld/user``)
  of the user.

* To send out content to the network, a new server should Follow other users on other servers
  to create social relationships. Public content will also be sent out to the servers whose
  users *you* follow, not just who follow you.

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

This is a `known issue with stream caching <https://git.feneas.org/socialhome/socialhome/issues/567>`_.
Until it is fixed, ask your instance admin to manually clear your profile cache. It can be done with
the following command, on the machine where Redis is running.

::

    redis-cli --scan --pattern 'sh:streams:profile_all:<profile.id>:*' | xargs redis-cli del

Where ``<profile.id>`` should be replaced by the profile ID found via the Socialhome admin view.
