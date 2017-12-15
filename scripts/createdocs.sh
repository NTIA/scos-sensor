#!/bin/bash

set -e  # exit on error

# Install documentation into /docs

SCRIPT=$(basename ${BASH_SOURCE[0]})
NARGS=$#
if [[ $NARGS != 1 ]]; then
    echo "Usage: $SCRIPT URL_TO_OPENAPI2_JSON"
    echo "Try starting the development server (./src/manage.py runsslserver)"
    echo "and using http://localhost:8000/api/v1/schema"
    exit 1
fi

URL="$1"

REPO_ROOT=$(git rev-parse --show-toplevel)

APIDOCS_ROOT="${REPO_ROOT}/docs/api"

echo "fetching openapi.json"
curl -k -H "Content-type: application/openapi+json" $URL \
    | python -m json.tool > ${APIDOCS_ROOT}/openapi.json
echo "wrote ${APIDOCS_ROOT}/openapi.json"

echo "converting openapi.json to openapi.adoc"
docker run --rm -v ${APIDOCS_ROOT}:/opt swagger2markup/swagger2markup \
       convert \
       -i  /opt/openapi.json \
       -f /opt/openapi \
       -c /opt/swagger2markup.properties
echo "wrote ${APIDOCS_ROOT}/openapi.adoc"

# http://asciidoctor.org/news/2014/02/04/github-asciidoctor-0.1.4-upgrade-5-things-to-know/#5-table-of-contents
echo "adding table of contents to openapi.doc"
awk 'NR==2 {print ":toc:"; print ":toc-placement: preable"} 1' \
    ${APIDOCS_ROOT}/openapi.adoc \
    > ${APIDOCS_ROOT}/openapi.adoc.toc \
    && mv -f ${APIDOCS_ROOT}/openapi.adoc{.toc,}

echo "converting openapi.adoc to openapi.pdf"
docker run --rm -v ${APIDOCS_ROOT}:/documents asciidoctor/docker-asciidoctor \
       asciidoctor-pdf openapi.adoc
echo "wrote ${APIDOCS_ROOT}/openapi.pdf"
