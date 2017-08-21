#!/bin/bash

set -e  # exit on error

EXISTING_CONTAINERS=$(docker ps -aq -f name="scossensor_*")

if [[ -n $EXISTING_CONTAINERS ]]; then
    docker rm -f $EXISTING_CONTAINERS;
fi

REPO_ROOT=$(git rev-parse --show-toplevel)

# variables defined in env file will be exported into this script's environment:
set -a
source ${REPO_ROOT}/env

# To avoid substituting nginx variables, which also use the shell syntax,
# specify only the variables that will be used in our nginx config:
# Populate nginx config template to get an actual nginx config
envsubst '$DOMAINS' < ${REPO_ROOT}/nginx/conf.template > ${REPO_ROOT}/nginx/conf.d/scos-sensor.conf

# Modify the Dockerfile template for our architecture
envsubst '$UBUNTU_IMAGE' < ${REPO_ROOT}/docker/Dockerfile.template > ${REPO_ROOT}/Dockerfile

# Populate the variables in compose file template and build
docker-compose -f ${REPO_ROOT}/docker/docker-compose.yml -p scossensor build
