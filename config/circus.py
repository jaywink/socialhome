from time import sleep

from django.db import connections, DEFAULT_DB_ALIAS
from django.db.migrations.executor import MigrationExecutor


def wait_until_database_synchronized(*args, **kwargs):
    """
    Wait until database synchronized.
    Return True when done, False if not done in 360 seconds.
    """
    counter = 0
    while True:
        counter += 1
        connection = connections[DEFAULT_DB_ALIAS]
        connection.prepare_database()
        executor = MigrationExecutor(connection)
        targets = executor.loader.graph.leaf_nodes()
        if not executor.migration_plan(targets):
            return True
        else:
            sleep(1)
        if counter > 360:
            # Abort if over 120 seconds
            return False
