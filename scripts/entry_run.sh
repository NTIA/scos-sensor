#!/bin/bash

set -e  # exit on error

echo 'Starting Migrations'
python manage.py migrate

echo 'Starting Gunicorn'
exec gunicorn --bind :8000 sensor.wsgi --log-level ${GUNICORN_LOG_LEVEL}
