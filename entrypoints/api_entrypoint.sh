#!/bin/bash

set -e  # exit on error

DB_PATH=/db.sqlite3

if [ -d $DB_PATH ]; then
    echo "The database file $DB_PATH didn't exist, so Docker mounted it as a directory."
    echo "Use the following commands to fix the issue:"
    echo "$ docker-compose stop"
    echo "$ docker-compose rm"
    echo "$ ./scripts/init_db.sh"
    exit 1
fi

echo "Starting Migrations"
python manage.py migrate

echo "Creating Superuser"
python /scripts/create_superuser.py

echo "Starting Gunicorn"
exec gunicorn sensor.wsgi -c ../gunicorn/config.py
