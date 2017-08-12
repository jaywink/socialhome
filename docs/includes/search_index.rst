The search indexes must be initialized, otherwise there will be an error when trying to use search. Run this command once:

::

    python manage.py rebuild_index

Any further changes to indexes objects will be maintained automatically from this point onwards. If you ever need to rebuild the index from scratch, use the same command.
