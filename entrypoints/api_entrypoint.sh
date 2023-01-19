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
# This is done to avoid loading actions and connecting to the sigan when migrations are applied and when
# the super user is created.
cp sensor/migration_settings.py sensor/settings.py
echo "Starting Migrations"
python3.8 manage.py migrate


echo "Creating superuser (if managed)"
python3.8 /scripts/create_superuser.py
cp sensor/runtime_settings.py sensor/settings.py

echo "Starting Gunicorn"
exec gunicorn sensor.wsgi -c ../gunicorn/config.py &
wait
