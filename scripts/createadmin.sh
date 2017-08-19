#!/bin/bash

set -e  # exit on error

docker-compose run api python manage.py createsuperuser

if $?; then
    docker commit $(docker ps -ql) scos-sensor
fi
