#!/bin/bash
# This script is called by Jenkins for running tests inside docker container.


pip install tox

cd /src
tox -e jenkins
