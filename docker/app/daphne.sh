#!/bin/sh
/usr/local/bin/python /app/manage.py migrate --noinput
/usr/local/bin/daphne -p 23564 config.asgi:application -v1 --proxy-headers
