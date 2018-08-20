#!/bin/bash

REPO_ROOT=${REPO_ROOT:=$(git rev-parse --show-toplevel)}
PROGRAM_NAME=${0##*/}
APP="$1"
SUCCESS=0


echo_usage() {
    cat << EOF
Backup location to a fixture file.
Backup is saved in ./src/{app}/fixtures/YYYY-MM-DD.json.

Usage: $PROGRAM_NAME app

Example:
    $PROGRAM_NAME capabilities
    [...]
    Wrote location backup to ./src/capabilities/fixtures/2018-02-22.json.

EOF

    exit 0
}


if [[ ! "$APP" || "$APP" == "-h" || "$APP" == "--help" ]]; then
    echo_usage
    exit 0
fi


OUTPUT_FILE=${REPO_ROOT}/src/status/fixtures/$(date -I).json

DB_RUNNING=$(docker-compose -f ${REPO_ROOT}/docker-compose.yml ps db |grep Up)
API_RUNNING=$(docker-compose -f ${REPO_ROOT}/docker-compose.yml ps api |grep Up)

# Ensure database container is running
docker-compose -f ${REPO_ROOT}/docker-compose.yml up -d db

echo "Querying $APP fixture"
echo "=============================="

if [[ "$API_RUNNING" ]]; then
    (docker-compose -f ${REPO_ROOT}/docker-compose.yml exec api \
                   /bin/bash -c "/src/manage.py dumpdata $APP --indent=4" && SUCCESS=1) \
                   1> >(tee "$OUTPUT_FILE") \
                   2>&1
else
    (docker-compose -f ${REPO_ROOT}/docker-compose.yml run --rm api \
                   /bin/bash -c "/src/manage.py dumpdata $APP --indent=4" && SUCCESS=1) \
                   1> >(tee "$OUTPUT_FILE") \
                   2>&1
fi

echo "=============================="

# If the DB was already running, leave it up
if [[ ! "$DB_RUNNING" ]]; then
    # Stop database container
    docker-compose -f ${REPO_ROOT}/docker-compose.yml stop db
fi

if [[ $SUCCESS ]]; then
    echo "Wrote location backup to $OUTPUT_FILE."
else
    echo "Backup failed" >&2
fi
