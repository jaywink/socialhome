#!/bin/sh
python /app/manage.py migrate --noinput
python /app/manage.py collectstatic --noinput
exec circusd /app/config/circus.ini

