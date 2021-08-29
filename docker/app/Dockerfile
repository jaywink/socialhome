FROM python:3.7-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /

RUN apt-get update && apt-get install python3-dev less htop curl git build-essential -y

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

RUN mkdir /usr/local/nvm

ENV NVM_DIR /usr/local/nvm
ENV NODE_VERSION 10.24.1

# Install nvm with node and npm
RUN curl https://raw.githubusercontent.com/creationix/nvm/v0.33.11/install.sh | bash \
    && source $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default

ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH      $NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH

COPY package.json ./
RUN npm install

COPY bower.json ./
RUN node_modules/.bin/bower --allow-root install

COPY docker/app/gunicorn.sh /gunicorn.sh
RUN chmod +x /gunicorn.sh

COPY . /app

RUN ln -s /node_modules /app/node_modules
RUN ln -s /bower_components /app/bower_components

WORKDIR /app/socialhome/frontend

RUN npm install

WORKDIR /app

RUN npm run build

RUN rm -rf /node_modules
RUN rm -rf /app/socialhome/frontend/node_modules
RUN rm -rf /bower_components
RUN rm -rf /root/.cache/Cypress

RUN cp config/circus_docker.ini config/circus.ini

RUN mkdir -p /logs

RUN pip install -U pip setuptools pip-tools

RUN pip-sync requirements/requirements.txt

RUN pip install gunicorn

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
ENV SOCIALHOME_RELAY_SCOPE=none

CMD circusd /app/config/circus.ini
