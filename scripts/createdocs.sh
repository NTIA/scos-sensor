#!/bin/bash

# Install documentation into /docs

REPO_ROOT=$(git rev-parse --show-toplevel)

APIDOCS_ROOT="${REPO_ROOT}/docs/api"

# FIXME: this is using a dummy swagger.json: change input
# swagger.json -> swagger.adoc
docker run --rm -v ${APIDOCS_ROOT}:/opt swagger2markup/swagger2markup \
       convert \
       -i http://petstore.swagger.io/v2/swagger.json \
       -f /opt/openapi \
       -c /opt/swagger2markup.properties
echo "wrote ${APIDOCS_ROOT}/openapi.adoc"

# openapi.adoc -> openapi.pdf
docker run --rm -v ${APIDOCS_ROOT}:/documents asciidoctor/docker-asciidoctor \
       asciidoctor-pdf openapi.adoc
echo "wrote ${APIDOCS_ROOT}/openapi.pdf"

# openapi.adoc -> html
docker run --rm -v ${APIDOCS_ROOT}:/documents asciidoctor/docker-asciidoctor \
       asciidoctor -a toc=left openapi.adoc
echo "wrote ${APIDOCS_ROOT}/openapi.html"
