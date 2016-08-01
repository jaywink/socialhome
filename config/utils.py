import os

def load_local_environment():
    """Load local env variables from the env.local file."""
    with open("env.local") as envfile:
        for line in envfile:
            if line.strip():
                setting = line.strip().split("=", maxsplit=1)
                os.environ.setdefault(setting[0], setting[1])
