#!/bin/bash

REPO_ROOT=$(git rev-parse --show-toplevel)

docker build -f ${REPO_ROOT}/Dockerfile -t ntiaits/test_scossensor_api ${REPO_ROOT}
