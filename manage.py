#!/usr/bin/env python
import os
import sys
import warnings


if __name__ == "__main__":
    # Load environment variables from env.local.
    # Good for injecting environment into PyCharm run configurations for example and no need to
    # manually load the env values for manage.py commands
    try:
        with open("env.local") as envfile:
            for line in envfile:
                if line.strip():
                    setting = line.strip().split("=", maxsplit=1)
                    os.environ.setdefault(setting[0], setting[1])
        # Backwards compatibility, since we used to require this and Django will freak out if here
        # TODO: Remove in some future date
        if "--load-env" in sys.argv:
            warnings.warn("Argument '--load-env' has been deprecated and will be removed in the future.")
            sys.argv.remove("--load-env")
    except FileNotFoundError:
        warnings.warn("Config file 'env.local' is missing. It should be created from 'env.example' with "
                      "necessary values replaced.")

    # Fail safe settings module
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
