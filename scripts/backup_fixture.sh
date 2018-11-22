#!/bin/bash

REPO_ROOT=${REPO_ROOT:=$(git rev-parse --show-toplevel)}
PROGRAM_NAME=${0##*/}
APP="$1"
OUTPUT_FILE="$2"
SUCCESS=0


echo_usage() {
    cat << EOF
Backup app state to a to a JSON "fixture" file.

Usage: $PROGRAM_NAME app output_file

Example:
    $PROGRAM_NAME capabilities backup.json
    [...]
    Wrote capabilities backup to ./backup.json.

EOF

    exit 0
}


if [[ ! "$APP" || ! "$OUTPUT_FILE" || "$APP" == "-h" || "$APP" == "--help" ]]; then
    echo_usage
    exit 0
fi


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
    echo "Wrote $APP backup to $OUTPUT_FILE."
else
    echo "Backup failed" >&2
fi
