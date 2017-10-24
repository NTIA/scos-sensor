#!/bin/bash

#
# Generate a UML diagram of database tables and models.
#

set -e  # exit on error

REPO_ROOT=$(git rev-parse --show-toplevel)

sudo apt-get install libgraphviz-dev

pip install pygraphviz

python ${REPO_ROOT}/src/manage.py graph_models --all-applications \
       --output ${REPO_ROOT}/docs/img/database_uml.svg

echo "Wrote ${REPO_ROOT}/docs/img/database_uml.svg"
