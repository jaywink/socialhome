FROM python:3.6

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install python-dev python3-dev -y

COPY requirements/requirements.txt ./

RUN pip install -U pip setuptools pip-tools

RUN pip-sync requirements.txt

# TODO use uwsgi or move to reqs
RUN pip install gunicorn

COPY . /app

RUN mkdir -p /logs

RUN groupadd -r django \
    && useradd -r -g django django

COPY docker/app/gunicorn.sh /gunicorn.sh

RUN sed -i 's/\r//' /gunicorn.sh \
    && chmod +x /gunicorn.sh \
    && chown django /gunicorn.sh

WORKDIR /app

RUN chown -R django /app

ENV POSTGRES_PASSWORD postgres
ENV RQWORKER_NUM 5
ENV DJANGO_SETTINGS_MODULE config.settings.production
ENV REDIS_HOST redis
ENV DATABASE_URL postgres://postgres:$POSTGRES_PASSWORD@db:5432/postgres
ENV DJANGO_SECURE_SSL_REDIRECT True
ENV DJANGO_DEBUG False
ENV DJANGO_ALLOWED_HOSTS socialhome.local
ENV DBHOST=db

CMD bash -c "./utils/wait-for-it/wait-for-it.sh --strict --timeout=10 $DBHOST:5432 && circusd /app/config/circus.ini"
