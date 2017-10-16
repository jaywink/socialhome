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

# NodeJS
RUN set -eu && \
    wget --quiet -O - https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - && \
    echo "deb https://deb.nodesource.com/node_6.x xenial main" | tee /etc/apt/sources.list.d/nodesource.list && \
    echo "deb-src https://deb.nodesource.com/node_6.x xenial main" | tee -a /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && apt-get install -y nodejs

# Copy the whole app
COPY . /home/socialhome/socialhome

# Ensure user owns everything
RUN set -eu && \
    chown -R socialhome:socialhome /home/socialhome

# Switch to Socialhome user
USER socialhome
WORKDIR /home/socialhome/socialhome

ENV DJANGO_SETTINGS_MODULE=config.settings.production

# Set permissions,
# install dependencies,
# install and build node stuff,
# collect statics using dummy secret key for the build process
RUN set -eu && \
    virtualenv -p /usr/bin/python3 .venv && \
    .venv/bin/pip install -U pip setuptools && \
    .venv/bin/pip install -r requirements.txt && \
    npm install && \
    node_modules/.bin/bower install && \
    node_modules/.bin/grunt build && \
    npm run dev && \
    DJANGO_SECRET_KEY=xxx .venv/bin/python manage.py collectstatic --no-input

# Run uWSGI
CMD ["/home/socialhome/socialhome/.venv/bin/uwsgi", "--ini", "/home/socialhome/socialhome/docker/django/uwsgi.ini"]

EXPOSE 8000
