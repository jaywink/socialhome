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

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

RUN mkdir /usr/local/nvm

ENV NVM_DIR /usr/local/nvm
ENV NODE_VERSION 8.9.0

# Install nvm with node and npm
RUN curl https://raw.githubusercontent.com/creationix/nvm/v0.33.11//install.sh | bash \
    && source $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default

ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH      $NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH

RUN npm install

RUN node_modules/.bin/bower --allow-root install

RUN npm run build

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

#CMD bash -c "./utils/wait-for-it/wait-for-it.sh --strict --timeout=10 $DBHOST:5432 && circusd /app/config/circus.ini"
CMD circusd /app/config/circus.ini
