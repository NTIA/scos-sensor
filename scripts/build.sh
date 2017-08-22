#!/bin/bash

# This script is idempotent, meaning it will remove state from previous
# deployments. That includes resetting containers and the database.

set -e  # exit on error

echo "Removing containers from previous deploys"
EXISTING_CONTAINERS=$(docker ps -aq -f name="scossensor_*")
if [[ -n $EXISTING_CONTAINERS ]]; then
    docker rm -f $EXISTING_CONTAINERS;
fi

REPO_ROOT=$(git rev-parse --show-toplevel)

echo "Resetting database"
truncate -s 0 ${REPO_ROOT}/db.sqlite3

# Inherit environment variables from env:
set -a
source ${REPO_ROOT}/env

# To avoid substituting nginx variables, which also use the shell syntax,
# specify only the variables that will be used in our nginx config: Populate
# nginx config template to get an actual nginx config
echo "Writing ${REPO_ROOT}/nginx/conf.d/scos-sensor.conf"
mkdir -p ${REPO_ROOT}/nginx/conf.d
envsubst '$DOMAINS' \
         < ${REPO_ROOT}/nginx/conf.template \
         > ${REPO_ROOT}/nginx/conf.d/scos-sensor.conf

echo "Modifying Dockerfile with base image ${UBUNTU_IMAGE}"
envsubst '$UBUNTU_IMAGE' \
         < ${REPO_ROOT}/docker/Dockerfile.template \
         > ${REPO_ROOT}/Dockerfile

echo "Calling docker-compose build"
docker-compose -f ${REPO_ROOT}/docker/docker-compose.yml -p scossensor build

echo "Initializing database schema"
docker-compose -f ${REPO_ROOT}/docker/docker-compose.yml -p scossensor \
               run api bash -c "python manage.py makemigrations && \
                                python manage.py migrate"
