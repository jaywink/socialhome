FROM python:3.9-slim

ENV PYTHONUNBUFFERED 1
ENV NVM_DIR /usr/local/nvm
ENV NODE_VERSION 12.22.12

WORKDIR /

# Install nvm with node and npm
RUN apt-get update && apt-get install python3-dev less htop curl git build-essential libmagic1 -y && \
    rm /bin/sh && ln -s /bin/bash /bin/sh && mkdir /usr/local/nvm && \
    curl https://raw.githubusercontent.com/creationix/nvm/v0.39.3/install.sh | bash

RUN source $NVM_DIR/nvm.sh && \
    nvm install $NODE_VERSION && \
    nvm alias default $NODE_VERSION && \
    nvm use default

ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH      $NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH

COPY package.json ./
COPY bower.json ./
COPY docker/app/start_socialhome.sh /start_socialhome.sh

RUN npm install && \
    node_modules/.bin/bower --allow-root install && \
    chmod +x /start_socialhome.sh && \
    mkdir -p /app/socialhome/frontend

COPY socialhome/frontend/package.json /app/socialhome/frontend
COPY socialhome/frontend/package-lock.json /app/socialhome/frontend

WORKDIR /app/socialhome/frontend

RUN npm install && \
    ln -s /node_modules /app/node_modules && \
    ln -s /bower_components /app/bower_components

WORKDIR /app

COPY requirements/requirements.txt ./

RUN pip install -U pip setuptools pip-tools && \
    pip-sync requirements.txt

COPY . /app

RUN npm run build && \
    rm -rf /node_modules && \
    rm -rf /app/socialhome/frontend/node_modules && \
    rm -rf /bower_components && \
    rm -rf /root/.cache/Cypress && \
    apt-get purge python3-dev build-essential -y && \
    apt autoremove -y && \
    cp config/circus_docker.ini config/circus.ini && \
    mkdir -p /logs

ENV POSTGRES_PASSWORD postgres
ENV RQWORKER_NUM 1
ENV DAPHNE_WORKER_NUM 1
ENV DJANGO_SETTINGS_MODULE config.settings.production
ENV REDIS_HOST redis
ENV DATABASE_URL postgres://postgres:$POSTGRES_PASSWORD@db:5432/postgres
ENV DJANGO_SECURE_SSL_REDIRECT True
ENV DJANGO_DEBUG False
ENV DJANGO_ACCOUNT_ALLOW_REGISTRATION=False
ENV DJANGO_ALLOWED_HOSTS socialhome.local
ENV DBHOST=db
ENV SOCIALHOME_LOG_TARGET=console

CMD /start_socialhome.sh
