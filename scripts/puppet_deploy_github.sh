#!/bin/bash

# This script is called during the first Github Puppet run to initialize the
# system, deploy the scos-sensor code, and run. This avoids rebooting the
# system to pick up the environment variables and various deployment/dependency
# timing issues. I.e. Puppet is not good at single run/deployment stuff.

id -u postgres > /dev/null
if [ $? -ne 0 ]
then
  set -e # exit on error
  useradd -s /usr/sbin/nologin postgres
fi

set -e # exit on error
cd $REPO_ROOT
# if [ ! -d "./data" ]
# then
#   mkdir ./data
# fi

chown postgres:postgres ./dbdata
export POSTGRES_USER=$(id -u postgres):$(id -g postgres)

docker-compose up -d
touch .deployed
touch .github
