#!/bin/sh

# Ensure that the database is a file and exists.
# Django handles schema initialization.

REPO_ROOT=${REPO_ROOT:=$(git rev-parse --show-toplevel)}
DB_PATH=${REPO_ROOT}/db.sqlite3

if [ -d $DB_PATH ]; then
    echo "The database file $DB_PATH didn't exist, so Docker mounted it as a directory."
    echo "Fixing... "
    rm -rf "$DB_PATH"
fi

echo "Ensuring $DB_PATH exists..."
touch "$DB_PATH"
