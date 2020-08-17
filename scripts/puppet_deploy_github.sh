#!/bin/bash

# This script is called during the first Github Puppet run to initialize the
# system, deploy the scos-sensor code, and run. This avoids rebooting the
# system to pick up the environment variables and various deployment/dependency
# timing issues. I.e. Puppet is not good at single run/deployment stuff.

set -e # exit on error

cd $REPO_ROOT
export PASSPHRASE="$(python3 scripts/generate_passphrase.py 64)"
docker-compose up -d
touch .deployed
touch .github
