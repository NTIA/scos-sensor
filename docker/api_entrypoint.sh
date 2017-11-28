#!/bin/bash

set -e  # exit on error

echo 'Starting Migrations'
python manage.py migrate

echo 'Creating Superuser'
python /scripts/create_superuser.py

echo 'Starting Gunicorn'
exec gunicorn --bind :8000 sensor.wsgi \
     --worker-class gthread --threads $nthreads \
     --log-level ${GUNICORN_LOG_LEVEL}
