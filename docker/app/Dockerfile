FROM python:3.8-slim

ENV PYTHONUNBUFFERED 1
ENV NVM_DIR /usr/local/nvm
ENV NODE_VERSION 10.24.1

WORKDIR /

# Install nvm with node and npm
RUN apt-get update && apt-get install python3-dev less htop curl git build-essential libmagic1 -y

RUN rm /bin/sh && ln -s /bin/bash /bin/sh && mkdir /usr/local/nvm && \
    curl https://raw.githubusercontent.com/creationix/nvm/v0.33.11/install.sh | bash

RUN source $NVM_DIR/nvm.sh && \
    nvm install $NODE_VERSION && \
    nvm alias default $NODE_VERSION && \
    nvm use default

ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH      $NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH

COPY package.json ./
COPY bower.json ./
COPY docker/app/gunicorn.sh /gunicorn.sh

RUN npm install && \
    node_modules/.bin/bower --allow-root install && \
    chmod +x /gunicorn.sh

COPY . /app

RUN ln -s /node_modules /app/node_modules && \
    ln -s /bower_components /app/bower_components

WORKDIR /app/socialhome/frontend

RUN npm install

WORKDIR /app

RUN npm run build && \
    rm -rf /node_modules && \
    rm -rf /app/socialhome/frontend/node_modules && \
    rm -rf /bower_components && \
    rm -rf /root/.cache/Cypress && \
    cp config/circus_docker.ini config/circus.ini && \
    mkdir -p /logs && mkdir /tmp/socialhome-metrics && \
    pip install -U pip setuptools pip-tools && \
    pip-sync requirements/requirements.txt && \
    pip install gunicorn

ENV POSTGRES_PASSWORD postgres
ENV RQWORKER_NUM 1
ENV DJANGO_SETTINGS_MODULE config.settings.production
ENV REDIS_HOST redis
ENV DATABASE_URL postgres://postgres:$POSTGRES_PASSWORD@db:5432/postgres
ENV DJANGO_SECURE_SSL_REDIRECT True
ENV DJANGO_DEBUG False
ENV DJANGO_ACCOUNT_ALLOW_REGISTRATION=False
ENV DJANGO_ALLOWED_HOSTS socialhome.local
ENV DBHOST=db
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/socialhome-metrics
ENV SOCIALHOME_LOG_TARGET=console

CMD circusd /app/config/circus.ini
