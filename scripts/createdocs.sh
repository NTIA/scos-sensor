#!/bin/bash

set -e  # exit on error

# Install documentation into /docs

SCRIPT=$(basename ${BASH_SOURCE[0]})
NARGS=$#
if [[ $NARGS != 1 ]]; then
    echo "Usage: $SCRIPT URL_TO_OPENAPI2_JSON"
    echo "Try starting the development server (./src/manage.py runserver)"
    echo "and using http://localhost:8000/api/v1/schema"
    exit 1
fi

URL="$1"

REPO_ROOT=$(git rev-parse --show-toplevel)

APIDOCS_ROOT="${REPO_ROOT}/docs/api"

curl -s -H "Accept: application/openapi+json" $URL \
    | python -m json.tool > ${APIDOCS_ROOT}/openapi.json

docker run --rm -v ${APIDOCS_ROOT}:/opt swagger2markup/swagger2markup \
       convert \
       -i  /opt/openapi.json \
       -d /opt/openapi \
       -c /opt/swagger2markup.properties
echo "wrote ${APIDOCS_ROOT}/openapi/*.adoc"

docker run --rm -v ${APIDOCS_ROOT}:/opt swagger2markup/swagger2markup \
       convert \
       -i  /opt/openapi.json \
       -f /opt/openapi \
       -c /opt/swagger2markup.properties
echo "wrote ${APIDOCS_ROOT}/openapi.adoc"

echo "converting openapi.adoc to openapi.pdf"
docker run --rm -v ${APIDOCS_ROOT}:/documents asciidoctor/docker-asciidoctor \
       asciidoctor-pdf openapi.adoc
echo "wrote ${APIDOCS_ROOT}/openapi.pdf"

echo "cleaning up ${APIDOCS_ROOT}/openapi.adoc"
rm -f ${APIDOCS_ROOT}/openapi.adoc
