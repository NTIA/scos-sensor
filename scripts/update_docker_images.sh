#!/bin/bash

# This script updates the docker images and return 0 if no change, and 1 if new
# images are available.

set -e

CURRENT=$(docker-compose images -q |sort)
docker-compose pull
NEW=$(docker-compose images -q |sort)

[[ $CURRENT == $NEW ]]
