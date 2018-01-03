#!/bin/bash

# This script is triggered to cleanup the Puppet install on the 
# sensor if there is a source file change.

set -e # exit on error

cd $REPO_ROOT

# Only remove the database if deployment has occured via Github

if [ -e .github ] 
then
mv -f db.sqlite3 db.sqlite3_backup
fi

rm -f .deployed
rm -f .github
rm -f .dockerhub

# Only move the environment file if it exists

if [ -e /etc/environment ] 
then
mv -f /etc/environment /etc/environment_backup
fi

touch /etc/environment

# Clean up Docker images / containers if present

if [ ! "$(docker ps -aq)" = "" ]
then
docker stop $(docker ps -aq)
docker rm -f $(docker ps -aq)
fi

if [ ! "$(docker images -q)" = "" ]
then
docker rmi -f $(docker images -q)
fi