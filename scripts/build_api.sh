#!/bin/bash

set -e  # exit on error

REPO_ROOT=${REPO_ROOT:=$(git rev-parse --show-toplevel)}

docker build -f ${REPO_ROOT}/Dockerfile -t smsntia/scos-sensor ${REPO_ROOT}
