.. _roadmap:

Roadmap
=======

Here we try to detail some future higher level plans for Socialhome.

Architecture
------------

Our current and future (dotted lines) architecture looks something like this:

.. image:: _static/architecture.png

At the lowest level we have the database (**PostgreSQL**) and **Redis** based cache / queue storage. To these we want to add some search index for full text search, possibly **Elasticsearch**.

On top of this we have the background jobs, which are powered by **RQ**.

In the middle sits **Django**.

To provide data for the frontend we have 3 solutions - **WebSockets** (powered by **Channels**), a **REST API** powered by **Django REST framework** and **Django** template engine itself.

For the frontend, we will have 3 solutions. Currently everything is **Django templates**. We will want to keep some of the pages as Django templates. For the streams (and possibly other pages), we want to create a **Vue.js** app. Additionally, **mobile apps** would be provided.

Vue.js app(s)
.............

The current streams JavaScript is largely based on lots of **jQuery** events modifying the DOM. Since the streams can grow to be quite big, this results in very bad performance. Additionally, the code is beginning to get hard to read and difficult to modify without regressions ("spaghetti code").

What we want to do is rewrite the streams as a more modern performant JS application. For the framework, discussion has been centering around **Vue.js**. The rationale is that Vue has the benefits of React.js with less overhead in learning curve and development time.

Why not replace the whole frontend with Vue.js? Simply because we want to use the best job for each software area. Some of the pages will not benefit from being rewritten in JavaScript. Django templates are powerful and fast to develop. But some parts, like the streams, will benefit hugely from features like the virtual DOM provided by Vue, in addition to allowing cleaner JavaScript code base.

Code layout
:::::::::::

Socialhome code layout is split into logical Django apps based on the feature provided. The JS code should follow this pattern and live in the respective app. For example for the ``streams`` Vue.js application, the following code layout would make sense:

::

    socialhome/
      streams/
        app/
          components/
            (components)
          App.vue
          main.js
        templates/
          streams/
            app.html
        views.py

Basically the idea is that ``views.py`` contains a Django view that loads the template inheriting from ``base.html``. The template then injects the Vue app, loading the stream. To speed up rendering we provide some initial stream data in the Django template context, then continuing everything via the REST API.

All the Vue apps build configuration should be on the top level of Socialhome, set up so all the apps build using the same ``npm`` commands. Each Vue.js app should however generate its own JS bundle file.

Code style
::::::::::

For the new Vue.js based JavaScript we should follow the popular `Airbnb guidelines <https://github.com/airbnb/javascript>`_ with the following exceptions:

* No semicolons. This is a Python project, we can go for more Pythonic looking JavaScript.

All code should be allowed ES7 features, using Babel to transpile.

Tests
:::::

We should use standard testing tools for the Vue apps code, for example **Karma** + **Mocha**.

Timeline
::::::::

Since this is a huge task which cannot be done at once, the new Vue.js based streams will be provided in addition to the current streams served by Django templates. This could be done in phases:

1. Alpha, little functionality - Render using Vue.js if a parameter `?vue` passed in the url.
2. Beta, most of the functionality present - Allow user to go to preferences and choose whether to see the new or legacy stream.
3. Final, all functionality covered - Make Vue based streams default, removing the old streams code.

Tracking issue
::::::::::::::

The Vue.js streams rewrite is tracked `in this issue <https://github.com/jaywink/socialhome/issues/202>`_.
