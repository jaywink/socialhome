#!/usr/bin/env python
import os
import sys


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

    # Load environment variables from env.local, if option --load-env specified.
    # Good for injecting environment into PyCharm run configurations for example and no need to
    # manually load the env values for manage.py commands
    if "--load-env" in sys.argv:
        with open("env.local") as envfile:
            for line in envfile:
                if line.strip():
                    setting = line.strip().split("=", maxsplit=1)
                    os.environ.setdefault(setting[0], setting[1])
        sys.argv.remove("--load-env")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
