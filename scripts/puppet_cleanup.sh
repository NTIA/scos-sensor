#!/bin/bash

# This script is triggered to cleanup the Puppet install on the
# sensor if there is a source file change.

set -e # exit on error

cd $REPO_ROOT

# Only remove the database if deployment has occured via Github

if [ -e .github ]; then
    if [ -e data ]; then
        rm -rf data
    fi
fi

rm -f .deployed
rm -f .github
rm -f .dockerhub

# Empty environment file
echo "" > /etc/environment

# Clean up Docker images / containers if present

if [ ! "$(docker ps -aq)" = "" ]; then
    docker stop $(docker ps -aq)
    docker rm -f $(docker ps -aq)
fi

if [ ! "$(docker images -q)" = "" ]; then
    docker rmi -f $(docker images -q)
fi
