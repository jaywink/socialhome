#!/usr/bin/env bash

#####################
# Release to Docker #
#####################
#
# Builds the image and pushes it to Docker Hub.
#
# Args: tag name, defaults to "latest"
#

set -e

if [[ -z "$1" ]]; then
    tag=latest
else
    tag=$1
fi

docker login

docker build -f docker/app/Dockerfile -t jaywink/socialhome:${tag} .
docker push jaywink/socialhome:${tag}
