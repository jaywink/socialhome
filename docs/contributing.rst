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

We have an `issue tracker <https://gitlab.com/jaywink/socialhome/-/issues>`_ on GitHub. If you don't already have an idea
on what to do, check out the issues listed there. Some issues are
`labeled as newcomer <https://gitlab.com/jaywink/socialhome/-/boards/4055970>`_.
These are easy picking tasks for those either new to Socialhome or with less knowledge of Django.

Logging issues
--------------

Contributions are not just code. Please feel free to log not only bugs but also enhancement ideas in the issue tracker.
For issues that have not been confirmed (= they don't have the label "ready"), triaging is important contribution
also. Reproducing and supplying more information on these issues is valuable contributon to the project.

:ref:`reporting-security-issues`

Writing code
------------

So you're ready to write code! Great! Please remember though that the project already has a vision, the software has
architecture and the project maintainer will have strong opinions on how things should be implemented. Before you
write a lot of code that even remotely feels like it would need a design decision, please *always* discuss your
plan first with the project maintainer. Otherwise you might spend a lot of time writing code only to be told the code
will not be merged because it doesn't fit into the grand plan.

Please don't be afraid to get in touch, see channels in the :ref:`community` pages.

Creating pull requests
----------------------

Before submitting a pull request, please ensure you've read and understood the following checklist.

.. include:: PULL_REQUEST_TEMPLATE.txt

Reviewing code
--------------

Code review is a valuable way to contribute, and also to learn about the code base! Don't be afraid to give some comments to `open merge requests <https://gitlab.com/jaywink/socialhome/-/merge_requests>`_! You don't have to be a veteran or know everything to be able to give opinions. Pull request reviews are not just for reviewing, they're a valuable opportunity for learning too.

Tests
-----

As a general rule all code must have unit tests. For bug fixes provide a test that ensures the bug will not be back
and for features always add a good enough coverage. PR's without sufficient test coverage will not be merged.

Testing tools
.............

Django
''''''

We use ``py.test`` as test runner but the tests themselves are Django based test classes. We have our own `base classes <http://gitlab.com/jaywink/socialhome/blob/master/socialhome/tests/utils.py>`_ which should be used as a base for all Django tests. Some old tests are pure py.test function based tests, feel free to convert these to Django test classes.

Focus is placed in pure unit tests instead of complex integration or browser tests. In terms of coverage, 100% is not the key, meaningful tests and coverage of critical lines is. Don't worry if a PR drops coverage a bit if the coverage diff clearly shows all critical code paths are covered by meaningful tests.

Vue
'''

The JS tests are using the `Avoriaz <https://eddyerburgh.gitbooks.io/avoriaz/content/>`_ Vue test utils and `Mocha <https://mochajs.org/>`_ test runner.

Code style
----------

Python
......

As a general rule, for Python code follow PEP8, except with a 120 character line length. We provide an
``.editorconfig`` in the repository root.

JavaScript
..........

There is an ``.eslintrc`` configuration provided.

Alphabetical ordering
.....................

When possible, try to always make all list items, dict keys, class methods, classes / functions in file, etc, everything alphabetically organized. This helps finding things when files grow and classes get a lot of methods. Sometimes this is not possible, for example when classes subclass another class in the same file. In this case for example, alphabetical ordering can be forgotten for logical placement.

Python dependencies
-------------------

.. include:: includes/pip_tools.rst
