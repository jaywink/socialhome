#!/bin/sh

set -eu

# basic build dependencies of various Django apps for Alpine 3.6
apk -U add \
  `# build-base metapackage install: binutils, fortify-headers, g++, gcc, libc-dev, make` \
  build-base \
  `# required to translate` \
  gettext \
  python2-dev \
  `# shared dependencies of Pillow, pylibmc` \
  zlib-dev \
  `# Postgresql and psycopg2 dependencies` \
  postgresql-dev \
  `# Pillow dependencies` \
  tiff-dev \
  jpeg-dev \
  freetype-dev \
  lcms-dev \
  libwebp-dev \
  `# django-extensions` \
  graphviz-dev \
  `# hitch` \
  py-setuptools \
  python3-dev \
  py-virtualenv \
  py2-pip \
  firefox-esr \
  automake \
  libtool \
  readline \
  readline-dev \
  sqlite-dev \
  libxml2 \
  libxml2-dev \
  libressl-dev \
  bzip2-dev \
  wget \
  curl \
  llvm4 \
  `# federation` \
  libxml2-dev \
  libxslt-dev \
  python3-dev \
  `# socialhome` \
  git \
  linux-headers \
  nodejs \
  nodejs-npm \
  postgresql \
  redis

rc-service postgresql start
rc-update add postgresql

rc-service redis start
rc-update add redis
