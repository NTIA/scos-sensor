#!/bin/bash

# Exit on error
set -e

REPO_ROOT=${REPO_ROOT:=$(git rev-parse --show-toplevel)}
PROGRAM_NAME=${0##*/}
INPUT="$1"


echo_usage() {
    cat << EOF
Backup capabilities to a fixture file.
Current date and filetype is appended automatically.

Usage: $PROGRAM_NAME filename_root

Example:
    $PROGRAM_NAME greyhound
    [...]
    Wrote capabilities backup to ./src/capabilities/fixtures/greyhound-2018-02-22.json.

EOF

    exit 0
}


if [[ ! "$INPUT" || "$INPUT" == "-h" || "$INPUT" == "--help" ]]; then
    echo_usage
    exit 0
fi


OUTPUT_FILE=${REPO_ROOT}/src/capabilities/fixtures/"$INPUT"-$(date -I).json

set +e  # this command may "fail"
DB_RUNNING=$(docker-compose -f ${REPO_ROOT}/docker-compose.yml ps db |grep Up)
API_RUNNING=$(docker-compose -f ${REPO_ROOT}/docker-compose.yml ps api |grep Up)
set -e

# Ensure database container is running
docker-compose -f ${REPO_ROOT}/docker-compose.yml up -d db

echo "Querying capabilities fixture"
echo "=============================="

# tail +4 strips off the output from the USRP driver

if [[ "$API_RUNNING" ]]; then
    docker-compose  -f ${REPO_ROOT}/docker-compose.yml exec api \
                    /bin/bash -c "echo -e '\u001E' && /src/manage.py dumpdata capabilities --indent=4" \
        | tail +4 | tee "$OUTPUT_FILE"
else
    docker-compose  -f ${REPO_ROOT}/docker-compose.yml run --rm api \
                    /bin/bash -c "echo -e '\u001E' && /src/manage.py dumpdata capabilities --indent=4" \
        | tail +4 | tee "$OUTPUT_FILE"
fi

echo "=============================="

# If the DB was already running, leave it up
if [[ ! "$DB_RUNNING" ]]; then
    # Stop database container
    docker-compose -f ${REPO_ROOT}/docker-compose.yml stop db
fi

echo "Wrote capabilities backup to $OUTPUT_FILE."
