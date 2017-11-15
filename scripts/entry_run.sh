#!/bin/bash

set -e  # exit on error

# GUNICORN_LOG_LEVEL='info'

echo 'Starting Migrations'
python manage.py migrate

echo 'Starting Gunicorn'
gunicorn --bind :8000 sensor.wsgi --log-level ${GUNICORN_LOG_LEVEL}
