#!/bin/sh
# Bring the schema up to date, then hand off to the server.
#
# Migrations run here so that `docker compose up` is genuinely one command.
# This is a proof-of-concept convenience: a deployment runs migrations as a
# separate, observable step rather than racing N replicas against each other.
set -eu

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "entrypoint: applying migrations"
    python manage.py migrate --noinput
fi

exec "$@"
