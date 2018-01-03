#!/bin/bash

# This script is triggered to cleanup the Puppet install on the 
# sensor if there is a source file change.

set -e # exit on error

cd $REPO_ROOT

if [ -e .github ] 
then
mv -f db.sqlite3 db.sqlite3_backup
fi

rm -f .deployed
rm -f .github
rm -f .dockerhub

if [ -e /etc/environment ] 
then
mv -f /etc/environment /etc/environment_backup
fi

touch /etc/environment
docker stop $(docker ps -aq)
docker rm -f $(docker ps -aq)
docker rmi -f $(docker images -q)