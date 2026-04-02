#! /usr/bin/env bash

set -e
set -x

if [ "$SKIP_PRESTART_DB" = "true" ]; then
    echo "Skipping prestart database checks and migrations as SKIP_PRESTART_DB is set to true"
else
    # Let the DB start
    python app/backend_pre_start.py

    # Run migrations
    alembic upgrade head

    # Create initial data in DB
    python app/initial_data.py
fi
