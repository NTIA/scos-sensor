#!/bin/bash

# Autoformat python - sort imports and then "blacken" code

REPO_ROOT=${REPO_ROOT:=$(git rev-parse --show-toplevel)}
SRC_ROOT=${REPO_ROOT}/src

echo "Sorting imports with isort... "
seed-isort-config --application-directories=${SRC_ROOT} --settings-path=${SRC_ROOT}
isort -rc ${SRC_ROOT}
echo
echo "Formatting code with black... "
black ${SRC_ROOT}
