FROM ubuntu:16.04

# Generate some locales
RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
    && localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8
ENV LANG en_US.utf8

# Install OS packages
RUN apt-get update && apt-get install -y \
    # Direct dependencies for socialhome
    git python-virtualenv python3-setuptools python3-dev build-essential libpq-dev \
    # Federation
    libxml2-dev libxslt-dev lib32z1-dev \
    # Redis TODO move to own container
    redis-server \
    # Generic stuff for Ubuntu
    wget apt-transport-https apt-utils

# Add user
RUN groupadd -r socialhome && useradd --no-log-init -r -g socialhome socialhome

# NodeJS
RUN wget --quiet -O - https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
RUN echo "deb https://deb.nodesource.com/node_6.x xenial main" | tee /etc/apt/sources.list.d/nodesource.list
RUN echo "deb-src https://deb.nodesource.com/node_6.x xenial main" | tee -a /etc/apt/sources.list.d/nodesource.list
RUN apt-get update && apt-get install -y nodejs

# Copy the whole app
COPY . /home/socialhome/socialhome

# Ensure user owns everything
RUN chown -R socialhome:socialhome /home/socialhome

# Switch to Socialhome user
USER socialhome
WORKDIR /home/socialhome/socialhome

RUN virtualenv -p /usr/bin/python3 .venv

ENV DJANGO_SETTINGS_MODULE=config.settings.production

# Install dependencies
RUN .venv/bin/pip install -U pip setuptools
RUN .venv/bin/pip install -r requirements.txt

# Install and build node stuff
RUN npm install
RUN node_modules/.bin/bower install
RUN node_modules/.bin/grunt build
RUN npm run dev

# Collect statics
# Dummy secret key for the build process
RUN DJANGO_SECRET_KEY=xxx .venv/bin/python manage.py collectstatic --no-input

# Run uWSGI
CMD ["/home/socialhome/socialhome/.venv/bin/uwsgi", "--ini", "/home/socialhome/socialhome/docker/django/uwsgi.ini"]

EXPOSE 8000
