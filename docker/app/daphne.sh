#!/bin/sh
/usr/local/bin/python /app/manage.py migrate --noinput
/usr/local/bin/python /app/manage.py collectstatic --noinput
/usr/local/bin/daphne -b 0.0.0.0 -p 23564 config.asgi:application -v1 --proxy-headers
