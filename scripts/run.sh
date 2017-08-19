#!/bin/bash

set -e  # exit on error

# You must run ./deploy.sh once before calling this script

REPO_ROOT=$(git rev-parse --show-toplevel)

# variables defined in setenv.local will be exported into this script's environment:
set -a
source ${REPO_ROOT}/.env

docker-compose -f ${REPO_ROOT}/docker/docker-compose.yml -p scossensor_ up
