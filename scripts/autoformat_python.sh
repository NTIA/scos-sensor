#!/bin/bash

# Autoformat python - sort imports and then "blacken" code

REPO_ROOT=${REPO_ROOT:=$(git rev-parse --show-toplevel)}

echo "Sorting imports with isort... "
isort -rc ${REPO_ROOT}/src/
echo
echo "Formatting code with black... "
black ${REPO_ROOT}/src/
