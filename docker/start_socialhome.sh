#!/bin/sh
python /app/manage.py migrate --noinput
python /app/manage.py collectstatic --noinput
python /app/manage.py compilemessages
exec circusd /app/config/circus.ini

