#!/bin/bash

set -e  # exit on error

REPO_ROOT=$(git rev-parse --show-toplevel)

echo "Ensuring that the ${REPO_ROOT}/db.sqlite3 exists..."
touch ${REPO_ROOT}/db.sqlite3

# To avoid substituting nginx variables, which also use the shell syntax,
# specify only the variables that will be used in our nginx config: Populate
# nginx config template to get an actual nginx config

echo "Writing ${REPO_ROOT}/nginx/conf.d/scos-sensor.conf"
mkdir -p ${REPO_ROOT}/nginx/conf.d
envsubst '$DOMAINS' \
         < ${REPO_ROOT}/nginx/conf.template \
         > ${REPO_ROOT}/nginx/conf.d/scos-sensor.conf


docker build -f ${REPO_ROOT}/Dockerfile -t ntiaits/test_scossensor_api ${REPO_ROOT}
