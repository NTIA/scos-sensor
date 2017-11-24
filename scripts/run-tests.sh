#!/bin/bash

set -e  # exit on error

# You must run ./deploy-tests.sh once before calling this script

REPO_ROOT=$(git rev-parse --show-toplevel)

# Stop running services
echo "Bringing down running services"
docker-compose -f ${REPO_ROOT}/docker-test/docker-compose.yml -p test_scossensor stop

# Build out and run in background
echo "Bringing up updated services"
docker-compose -f ${REPO_ROOT}/docker-test/docker-compose.yml -p test_scossensor up -d --build
