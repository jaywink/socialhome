.. _contributing:

Contributing
============

Want to contribute to Socialhome? Great! <3 Please read on for some guidelines.

First things first
------------------

Please make sure you have some knowledge of what the software is for before jumping in to write code.
You don't even have to install a development environment. Just head to https://socialhome.network, create an account
and play around.

If you already are a user or run your own instance, you probably have some ideas on how to contribute already.
The best contributions come from real personal need.

Finding things to do
--------------------

We have an `issue tracker <https://github.com/jaywink/socialhome/issues>`_) on GitHub. If you don't already have an idea
on what to do, check out the issues listed there. Some issues are
`labeled as newcomer <https://github.com/jaywink/socialhome/issues?q=is%3Aissue+is%3Aopen+label%3Anewcomer>`_.
These are easy picking tasks for those either new to Socialhome or with less knowledge of Django.

Logging issues
--------------

Contributions are not just code. Please feel free to log not only bugs but also enhancement ideas in the issue tracker.
For issues that have not been confirmed (= they don't have the label "ready"), triaging is important contribution
also. Reproducing and supplying more information on these issues is valuable contributon to the project.

Writing code
------------

So you're ready to write code! Great! Please remember though that the project already has a vision, the software has
architecture and the project maintainer will have strong opinions on how things should be implemented. Before you
write a lot of code that even remotely feels like it would need a design decision, please *always* discuss your
plan first with the project maintainer. Otherwise you might spend a lot of time writing code only to be told the code
will not be merged because it doesn't fit into the grand plan.

Please don't be afraid to get in touch, see channels in the :ref:`community` pages.

Feature notes
.............

Some notes regarding features to take into account when writing code.

Streams
:::::::

Everything is (supposed to be at least) a stream in Socialhome. The main streams are user profiles, followed and the public stream, but basically each single content view is also a stream. Opening a reply in an individual window would also create a stream for that reply content.

A stream should automatically subscribe the user using websockets and handle any incoming messages from the server (in ``socialhome/static/js/streams.js``), notifying the user of new content and adding it to the page on request (without a page load).

This basic design should be kept in mind when touching stream related code.

Stream templates
++++++++++++++++

Content in streams in is visualized mainly as content grid boxes. This includes replies too, which mainly use the same template code. Different from this is the single content view which is rendered with a slightly different template.

There are three locations to modify when changing how content is rendered in streams or single content views:

* ``socialhome/streams/templates/streams/base.html`` - This renders the initial stream as a basic Django template on page load.
* ``socialhome/static/js/content.js`` - This is the main JavaScript template which is used to insert content into the stream. This is used for both top level content and replies in content streams.
* ``socialhome/content/templates/content/_content_detail.html`` - This template is used to render the single content view either directly or as a pop-up modal (with data filled by JS).

All these three templates must be checked when any content rendering related tweaks are done. Note however that actual content Markdown rendering happens at save time, not in the templates.

Tests
-----

As a general rule all code must have unit tests. For bug fixes provide a test that ensures the bug will not be back
and for features always add a good enough coverage. PR's without sufficient test coverage will not be merged.

Testing tools
.............

We use ``py.test`` as test runner but the tests themselves are Django ``TestCase`` based test classes. We have our own base class called ``SocialhomeTestCase`` which should be used as a base for all Django tests. Some old tests are pure py.test function based tests, feel free to convert these.

Focus is placed in pure unit tests instead of complex integration or browser tests. In terms of coverage, 100% is not the key, meaningful tests and coverage of critical lines is. Don't worry if a PR drops coverage a bit if the coverage diff clearly shows all critical code paths are covered by meaningful tests.

We also have some ``Mocha`` based JavaScript tests. Any new JS code that affects for example streams functionality should have at least basic tests written.

Code style
----------

As a general rule, for Python code follow PEP8, except with a 120 character line length. We provide an
``.editorconfig`` in the repository root.
