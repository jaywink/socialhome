FROM ubuntu:16.04

# Generate some locales
RUN set -eu && \
    apt-get update && \
    apt-get install -y locales && \
    rm -rf /var/lib/apt/lists/* && \
    localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8

ENV LANG en_US.utf8

# Install OS packages:
# - direct dependencies for Socialhome
# - Federation
# - Redis TODO move to own container
# - generic stuff for Ubuntu
RUN set -eu && \
    apt-get update && \
    apt-get install -y \
        git python-virtualenv python3-setuptools python3-dev build-essential libpq-dev \
        libxml2-dev libxslt-dev lib32z1-dev \
        redis-server \
        wget apt-transport-https apt-utils

# Add user
RUN set -eu && \
    groupadd -r socialhome && \
    useradd --no-log-init -r -g socialhome socialhome

# Copy the whole app
COPY . /home/socialhome/socialhome

# Ensure user owns everything
RUN set -eu && \
    chown -R socialhome:socialhome /home/socialhome

# Switch to Socialhome user
USER socialhome
WORKDIR /home/socialhome/socialhome

# Bring in environment variables from compose
ARG DATABASE_URL
ARG DJANGO_SECRET_KEY
ARG DJANGO_ALLOWED_HOSTS
ARG DJANGO_SECURE_SSL_REDIRECT
ARG DJANGO_ACCOUNT_ALLOW_REGISTRATION
ARG SOCIALHOME_DOMAIN
ARG SOCIALHOME_HTTPS
ARG SOCIALHOME_LOGFILE
ARG SOCIALHOME_LOGFILE_FEDERATION
ARG DJANGO_ADMIN_NAME
ARG DJANGO_ADMIN_MAIL
ARG DJANGO_SERVER_EMAIL
ARG DJANGO_OPBEAT_ORGANIZATION_ID
ARG DJANGO_OPBEAT_APP_ID
ARG DJANGO_OPBEAT_SECRET_TOKEN
ARG DJANGO_AWS_ACCESS_KEY_ID
ARG SOCIALHOME_STATISTICS
ARG DJANGO_DEBUG_TOOLBAR
ARG MOCHA_TESTS
ARG DJANGO_SETTINGS_MODULE

ENV DATABASE_URL=$DATABASE_URL \
    DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY \
    DJANGO_ALLOWED_HOSTS=$DJANGO_ALLOWED_HOSTS \
    DJANGO_SECURE_SSL_REDIRECT=$DJANGO_SECURE_SSL_REDIRECT \
    DJANGO_ACCOUNT_ALLOW_REGISTRATION=$DJANGO_ACCOUNT_ALLOW_REGISTRATION \
    SOCIALHOME_DOMAIN=$SOCIALHOME_DOMAIN \
    SOCIALHOME_HTTPS=$SOCIALHOME_HTTPS \
    SOCIALHOME_LOGFILE=$SOCIALHOME_LOGFILE \
    SOCIALHOME_LOGFILE_FEDERATION=$SOCIALHOME_LOGFILE_FEDERATION \
    DJANGO_ADMIN_NAME=$DJANGO_ADMIN_NAME \
    DJANGO_ADMIN_MAIL=$DJANGO_ADMIN_MAIL \
    DJANGO_SERVER_EMAIL=$DJANGO_SERVER_EMAIL \
    DJANGO_OPBEAT_ORGANIZATION_ID=$DJANGO_OPBEAT_ORGANIZATION_ID \
    DJANGO_OPBEAT_APP_ID=$DJANGO_OPBEAT_APP_ID \
    DJANGO_OPBEAT_SECRET_TOKEN=$DJANGO_OPBEAT_SECRET_TOKEN \
    DJANGO_AWS_ACCESS_KEY_ID=$DJANGO_AWS_ACCESS_KEY_ID \
    SOCIALHOME_STATISTICS=$SOCIALHOME_STATISTICS \
    DJANGO_DEBUG_TOOLBAR=$DJANGO_DEBUG_TOOLBAR \
    MOCHA_TESTS=$MOCHA_TESTS \
    DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

# Install dependencies
RUN set -eu && \
    virtualenv -p /usr/bin/python3 .venv && \
    .venv/bin/pip install -U pip setuptools && \
    .venv/bin/pip install -r requirements.txt

# Run worker
CMD ["/home/socialhome/socialhome/.venv/bin/daphne", "config.asgi:channel_layer"]

EXPOSE 8000
