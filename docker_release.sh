#!/usr/bin/env bash

set -e

docker login

docker build -f docker/app/Dockerfile -t jaywink/socialhome .
docker push jaywink/socialhome:latest
