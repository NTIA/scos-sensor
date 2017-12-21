#!/bin/bash

set -e  # exit on error

echo 'Starting Migrations'
python manage.py migrate

echo 'Creating Superuser'
python /scripts/create_superuser.py

# The following starts and monitors 3 different services, from
# https://docs.docker.com/engine/admin/multi-service_container/.

# Start gunicorn
gunicorn sensor.wsgi -c ../gunicorn/config.py & gunicorn_pid=$!
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start gunicorn: $status"
  exit $status
fi

# Start the websocket worker
python manage.py runworker --only-channels=websocket.*  --threads=2 & ws_worker_pid=$!
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start websocket.* worker: $status"
  exit $status
fi

# Start Daphne interface server
daphne -b 0.0.0.0 -p 8001 --proxy-headers sensor.asgi:channel_layer & daphne_pid=$!
status=$?
if [ $status -ne 0 ]; then
  echo "Failed to start daphne interface server: $status"
  exit $status
fi


interruptable_sleep() {
    pid=
    trap '[[ $pid ]] && kill $pid; exit 0' TERM  # Kill sleep and exit if caught SIGTERM from Docker
    sleep $1 & pid=$!
    wait
    pid=
}


while true; do
    ps -p $gunicorn_pid > /dev/null
    GUNICORN_STATUS=$?
    ps -p $ws_worker_pid > /dev/null
    WS_WORKER_STATUS=$?
    ps -p $daphne_pid > /dev/null
    DAPHNE_STATUS=$?
    # If all are not 0, then something is wrong
    if [ $GUNICORN_STATUS -ne 0 -o $WS_WORKER_STATUS -ne 0 -o $DAPHNE_STATUS -ne 0 ]; then
        echo "One of the processes has already exited."
        exit -1
    fi
    interruptable_sleep 30
done
