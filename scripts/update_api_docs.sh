#!/bin/bash

set -e  # exit on error

# Install openapi.json into /docs

REPO_ROOT=$(git rev-parse --show-toplevel)
DOCS_ROOT="${REPO_ROOT}/docs"

echo "Generating openapi.json ..."

cd ${REPO_ROOT}/src
tox -e update-api-docs || tox -r -e update-api-docs

echo "Wrote ${REPO_ROOT}/docs/openapi.json"
