#!/bin/sh
/usr/local/bin/python /app/manage.py migrate --noinput
/usr/local/bin/python /app/manage.py collectstatic --noinput
/usr/local/bin/daphne --fd $CIRCUS_SOCKET_FD config.asgi:application -v1 --proxy-headers
