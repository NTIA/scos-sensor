#!/bin/bash

set -e  # exit on error

echo "Removing containers from previous deploys"
EXISTING_CONTAINERS=$(docker ps -aq -f name="test_scossensor_*")
if [[ -n $EXISTING_CONTAINERS ]]; then
    docker rm -f $EXISTING_CONTAINERS;
fi

REPO_ROOT=$(git rev-parse --show-toplevel)

echo "Modifying Dockerfile with base image ${UBUNTU_IMAGE}"
envsubst '$UBUNTU_IMAGE' \
         < ${REPO_ROOT}/docker-test/Dockerfile.template \
         > ${REPO_ROOT}/Dockerfile
