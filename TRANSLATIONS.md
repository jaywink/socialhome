Initialisation
--------------

Translations are hosted at https://translate.codeberg.org/projects/socialhome. During the initial setup, weblate will pull the django.pot file.
Then new translations can be started using weblate's UI. The pattern to configure for po files is socialhome/locale/*/LC_MESSAGES/django.po.

From the project directory, run the following command to create the initial pot file:

```
./manage.py makemessages -a --keep-pot
```

Then commit and push the modified files to master.

Note: this step should needed only once. If a pot file already exists, go to the next section.

Note: see the django documentation to learn how to localize the code.


Updating
--------

When new strings are added/updated/deleted to/from the code, update the pot file and existing po files using:
```
./manage.py makemessages --keep-pot --no-obsolete $(find socialhome/locale -maxdepth 1 -type d|tail -n +2|xargs -n1 basename|sed 's/^/-l /')
```

Then commit and push the modified files to master.


Saving and archiving from the weblate project will push the updated po files to socialhome's repository.

If manual changes to the translation template file (django.pot) are made, they should first be merged with all existing translations with (bash script example):

```
for f in locale/*/LC_MESSAGES/django.po; do
  msgmerge -U $f locale/django.pot # NOTE: pybabel update could also be used
done
```

Then commit and push. weblate should pick them up automatically via its configured webhook.

Building
--------

weblate can be configure to automatically compile mo files, but until we figure out how it works, use the following:
```
./manage.py compilemessages

If a docker used, this should be built-in into the image.
```

