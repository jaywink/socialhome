Requirements
------------

pybabel (already installed)
pip install django-babel (TODO: document my fix to extract.py)
pip install babel-vue-extractor

Create the initial pot file
---------------------------

From project directory,

Create babel.cfg with the following content:
```
[django: templates/**.*]
[django: socialhome/*/templates/**.*]
[python: socialhome/**.py]
[babelvueextractor.extract.extract_vue: socialhome/**.vue]
[javascript: socialhome/frontend/*.js]
[javascript: socialhome/frontend/src/**.js]
```

Extract initial pot file using:
```
pybabel extract -F babel.cfg -o socialhome/locale/django.pot .
```

TODO
----

Weblate setup.

Compile translations
--------------------

django-admin compilemessages
