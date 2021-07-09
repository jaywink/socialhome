Requirements
------------

pybabel (already installed)
pip install django-babel

Patch django-babel with (assuming you are using virtualenv):
```
patch -p1 ~/.virtualenvs/socialhome/lib/python3.9/site-packages/django_babel/extract.py < ~/socialhome/translate/django_babel.patch
```

TODO: create an issue for this

Workflow
--------

From project directory,

Create or update the pot file using:
```
PYTHONPATH=. pybabel extract -F babel.cfg -o socialhome/locale/django.pot .
```

Translations are hosted at https://hosted.weblate.org/projects/socialhome. During the initial setup, weblate will pull the django.pot file.
Then new translations can be started using weblate's UI. The pattern to configure for po files is socialhome/locale/*/LC_MESSAGES/django.po.

weblate can be configure to automatically compile mo files, but until we figure out how it works, use the following:
```
django-admin compilemessages
```

or (bash script example):

```
for f in locale/*/LC_MESSAGES/django.po; do
  msgfmt -o ${f/.po/.mo} $f
done
```

Saving and archiving from the weblate project will push the updated po files to socialhome's repository.

If manual changes to the translation template file (django.pot) are made, they should first be merged with all existing translations with (bash script example):

```
for f in locale/*/LC_MESSAGES/django.po; do
  msgmerge -U $f locale/django.pot # NOTE: pybabel update could also be used
done
```

Then commit and push. weblate should pick them up automatically via its configured gitlab webhook.



Hack
----

~/socialhome/translate/extract.py is a wrapper around pybabel's javascript extractor to deal with template literal placeholders and filters.

TODO: create an issue for this.

NOTE: pybabel is configured tp parse compiled js only. If changes are made to js or vue files, npm run dev should be run before updating the translation files.
