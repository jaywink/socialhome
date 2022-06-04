#!/usr/bin/env bash

#####################
# Release to Docker #
#####################
#
# Builds the image and pushes it to the Docker registry.
#
# Args:
#   tag name
#   "nolatest" if latest should not be updated as well.
#

set -e

if [[ -z "$1" ]]; then
    tag=latest
else
    tag=$1
fi

docker login registry.gitlab.com
docker build -f docker/app/Dockerfile -t registry.gitlab.com/jaywink/socialhome:${tag} .
docker push registry.gitlab.com/jaywink/socialhome:${tag}

if [[ "$2" == "nolatest" ]]; then
    exit
fi

docker tag registry.gitlab.com/jaywink/socialhome:${tag} registry.gitlab.com/jaywink/socialhome:latest
docker push registry.gitlab.com/jaywink/socialhome:latest
