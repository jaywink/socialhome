#!/usr/bin/env bash

#####################
# Release to Docker #
#####################
#
# Builds the image and pushes it to the Docker registry.
#
# Args:
#   tag name
#
# Pre-requisites:
# 	- qemu-user-static must be installed
# 	- bin_fmt kernel support
# 	- must run:
# 		sudo podman run --rm --privileged multiarch/qemu-user-static --reset -p yes
#	  if it has not been run since the last reboot
#
# Note: building foreign platforms might take a lot more time.

registry=codeberg.org
platforms=linux/amd64,linux/arm64
manifest=$registry/socialhome/socialhome

if [[ -z "$1" ]]; then
    echo "Usage: $0 tag"
    exit 1
else
    tag=$1
fi

buildah manifest rm $manifest
set -e

buildah build -f docker/app/Dockerfile --squash --jobs=2 --platform=$platforms --manifest $manifest .

buildah login $registry
buildah manifest push --all $manifest docker://$manifest:$tag

