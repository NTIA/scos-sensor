#!/bin/bash

# This script is called during the first Github Puppet run to initialize the
# system, deploy the scos-sensor code, and run. This avoids rebooting the
# system to pick up the environment variables and various deployment/dependency
# timing issues. I.e. Puppet is not good at single run/deployment stuff.

id -u postgres > /dev/null
if [ $? -ne 0 ]
then
  set -e # exit on error
  # create user for postgres alpine container
  groupadd -g 70 postgres
  useradd -s /usr/sbin/nologin -u 70 -g 70 postgres
fi

set -e # exit on error
cd $REPO_ROOT
rm -rf configs/certs/test # make sure test certs are not used in production
docker-compose up -d
touch .deployed
touch .github
