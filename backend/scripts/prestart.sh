#! /usr/bin/env bash

set -e
set -x

if [ "$SKIP_PRESTART_DB" = "true" ]; then
    echo "Skipping prestart database checks and migrations as SKIP_PRESTART_DB is set to true"
else
    # Let the DB start
    python app/backend_pre_start.py

    if [ "$SKIP_ALEMBIC" = "true" ]; then
        echo "Skipping Alembic migrations as SKIP_ALEMBIC is set to true"
    else
        # Run migrations
        alembic upgrade head
    fi

    # Create initial data in DB (this now also creates tables via SQLModel)
    python app/initial_data.py
fi
