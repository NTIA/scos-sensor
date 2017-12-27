#!/bin/bash

set -e  # exit on error

# Install documentation into /docs

SCRIPT=$(basename ${BASH_SOURCE[0]})
NARGS=$#
if [[ $NARGS != 2 ]]; then
    echo "Usage: $SCRIPT URL_TO_OPENAPI2_JSON API_TOKEN"
    echo ""
    echo "Try starting the development server (./src/manage.py runsslserver)"
    echo "and using https://localhost/api/v1/schema/?format=openapi."
    echo ""
    echo "To find your authentication token, log into the server and visit"
    echo "https://localhost/api/v1/users/me/."
    exit 1
fi

URL="$1"
API_TOKEN="$2"

REPO_ROOT=$(git rev-parse --show-toplevel)

DOCS_ROOT="${REPO_ROOT}/docs"

echo "fetching openapi.json"
curl $URL -k \
-H "Content-type: application/openapi+json" \
-H "Authorization: Token ${API_TOKEN}" \
> ${DOCS_ROOT}/swagger.json
echo "wrote ${APIDOCS_ROOT}/swagger.json"
