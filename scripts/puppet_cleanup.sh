#!/bin/bash

# This script is triggered to cleanup the Puppet install on the
# sensor if there is a source file change.

set -e # exit on error

cd $REPO_ROOT

rm -f .deployed
rm -f .github
rm -f .dockerhub

touch /etc/environment

# Clean up Docker images / containers if present

if [ ! "$(docker ps -aq)" = "" ]; then
    docker stop $(docker ps -aq)
    docker rm -f $(docker ps -aq)
fi

if [ ! "$(docker images -q)" = "" ]; then
    docker rmi -f $(docker images -q)
fi
