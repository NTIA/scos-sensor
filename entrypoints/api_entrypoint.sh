#!/bin/bash

function cleanup_demodb {
    local demodb_path=/src/demo-db.sqlite3
    if [[ -e $demodb_path ]]; then
        echo "Cleaning up demo db $demodb_path..."
        rm -f $demodb_path
    fi
}

trap cleanup_demodb SIGTERM
trap cleanup_demodb SIGINT
RUNNING_MIGRATIONS="True"
export RUNNING_MIGRATIONS
echo "Starting Migrations"
python3.9 manage.py migrate
RUNNING_MIGRATIONS="False"
echo "Starting Gunicorn"
exec gunicorn sensor.wsgi -c ../gunicorn/config.py &
wait
