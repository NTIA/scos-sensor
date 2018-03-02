#!/bin/bash

set -e  # exit on error

echo "Ensuring Migrations are up-to-date"
python manage.py makemigrations

echo "Starting Migrations"
python manage.py migrate

echo "Creating Superuser"
python /scripts/create_superuser.py

echo "Starting Gunicorn"
exec gunicorn sensor.wsgi -c ../gunicorn/config.py
