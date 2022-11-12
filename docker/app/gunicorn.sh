#!/bin/sh
export PROMETHEUS_MULTIPROC_DIR=/tmp/socialhome-metrics

/usr/local/bin/python /app/manage.py migrate --noinput
/usr/local/bin/python /app/manage.py collectstatic --noinput
/usr/local/bin/gunicorn config.wsgi -w 2 -b 0.0.0.0:5000 --chdir=/app --capture-output
