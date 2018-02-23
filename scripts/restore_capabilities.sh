#!/bin/bash

# Exit on error
set -e

REPO_ROOT=${REPO_ROOT:=$(git rev-parse --show-toplevel)}
PROGRAM_NAME=${0##*/}
INPUT="$1"


echo_usage() {
    cat << EOF
Restore capabilities from a fixture file.

Usage: $PROGRAM_NAME filename

Example:
    $PROGRAM_NAME ./src/capabilities/fixtures/greyhound-2018-02-22.json

EOF

    exit 0
}


if [[ ! "$INPUT" || "$INPUT" == "-h" || "$INPUT" == "--help" ]]; then
    echo_usage
    exit 0
fi

if [[ ! -e "$INPUT" ]]; then
    echo "Fixture file \"$INPUT\" doesn't exist."
    exit 1
fi

set +e  # this command may "fail"
DB_RUNNING=$(docker-compose -f ${REPO_ROOT}/docker-compose.yml ps db |grep Up)
set -e

# Ensure database container is running
docker-compose -f ${REPO_ROOT}/docker-compose.yml up -d db

# Load given fixture file into database
python ${REPO_ROOT}/src/manage.py loaddata "$INPUT"

# If the DB was already running, leave it up
if [[ ! "$DB_RUNNING" ]]; then
    # Stop database container
    docker-compose -f ${REPO_ROOT}/docker-compose.yml stop db
fi

echo "Restored capabilities from $INPUT."
