web: gunicorn config.wsgi:application
worker: celery worker --app=socialhome.taskapp --loglevel=info
