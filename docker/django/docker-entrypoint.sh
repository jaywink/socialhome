#!/bin/sh
#
# Example of an entrypoint for Python/Django apps
#

# Exit immediately if a command exits with a non-zero status.
# http://stackoverflow.com/questions/19622198/what-does-set-e-mean-in-a-bash-script
set -e

# Define help message
show_help() {
    echo """
Usage: docker run <imagename> COMMAND
Commands
dev     : Start a normal Django development server
migrat  : Run migrations
bash    : Start a bash shell
manage  : Start manage.py
python  : Run a python command
shell   : Start a Django Python shell
help    : Show this message
"""
}

PORT=8000

# Run
case "$1" in
    dev)
        echo "Running Development Server..."
        python manage.py runserver 0.0.0.0:${PORT}
    ;;
    migrate)
        python manage.py migrate
    ;;
    bash)
        /bin/bash "${@:2}"
    ;;
    manage)
        python manage.py "${@:2}"
    ;;
    shell)
        python manage.py shell_plus
    ;;
    *)
        show_help
    ;;
esac
