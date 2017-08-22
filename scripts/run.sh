#!/bin/bash

set -e  # exit on error

# You must run ./deploy.sh once before calling this script

REPO_ROOT=$(git rev-parse --show-toplevel)

# Inherit environment variables from env:
set -a
source ${REPO_ROOT}/env

# Build out and run in background
docker-compose -f ${REPO_ROOT}/docker/docker-compose.yml -p scossensor up -d
