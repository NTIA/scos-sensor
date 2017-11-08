#!/bin/bash

set -e  # exit on error

echo "Removing containers from previous deploys"
EXISTING_CONTAINERS=$(docker ps -aq -f name="test_scossensor_*")
if [[ -n $EXISTING_CONTAINERS ]]; then
    docker rm -f $EXISTING_CONTAINERS;
fi

REPO_ROOT=$(git rev-parse --show-toplevel)

# To avoid substituting nginx variables, which also use the shell syntax,
# specify only the variables that will be used in our nginx config: Populate
# nginx config template to get an actual nginx config
# echo "Writing ${REPO_ROOT}/nginx/conf.d/scos-sensor.conf"
# mkdir -p ${REPO_ROOT}/nginx/conf.d
# envsubst '$DOMAINS' \
#          < ${REPO_ROOT}/nginx/conf.template \
#          > ${REPO_ROOT}/nginx/conf.d/scos-sensor.conf

echo "Modifying Dockerfile with base image ${UBUNTU_IMAGE}"
envsubst '$UBUNTU_IMAGE' \
         < ${REPO_ROOT}/docker-test/Dockerfile.template \
         > ${REPO_ROOT}/Dockerfile
