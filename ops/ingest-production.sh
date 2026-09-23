#!/usr/bin/env bash
# Ingest one document into the production database, from this workstation.
#
#   ops/ingest-production.sh <file under sources/> <slug> [ingest_source options...]
#
# e.g.
#   ops/ingest-production.sh Acuerdo-Final-JEP-24-11-2016.pdf acuerdo-final-jep-2016 \
#       --language spanish --nickname "el acuerdo" --title "..." --edition "..."
#
# What it does, in order:
#   1. opens the database to this machine's public IP (OpenTofu, targeted
#      at the database only);
#   2. waits until the database accepts connections through the allowlist;
#   3. runs ingest_source, verify_anchors and embed_source from the local
#      stack's image, with DATABASE_URL pointed at production;
#   4. closes the database again — always, even when a step fails.
#
# The PDF never leaves this machine: only the parsed units and embeddings
# reach the database. Credentials come from ops/tofu/.env (OpenTofu) and
# dev/.env (the OpenAI key used for embeddings).

set -euo pipefail

usage() {
    sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'
    exit 2
}

[ $# -ge 2 ] || usage
FILE=$1
SLUG=$2
shift 2

ROOT=$(cd "$(dirname "$0")/.." && pwd)
TOFU_DIR=$ROOT/ops/tofu
TOFU_IMAGE=ghcr.io/opentofu/opentofu:1.12.6

[ -f "$TOFU_DIR/.env" ] || { echo "ops/tofu/.env is missing" >&2; exit 1; }
# Local test-bed documents are internal and must never reach production.
case "$(echo "$FILE" | tr '[:upper:]' '[:lower:]')" in
    *edunext*|*bcp*|*business*continuity*)
        echo "Refusing: '$FILE' is a local test-bed document, not a publishable source." >&2
        exit 1 ;;
esac

[ -f "$ROOT/sources/$FILE" ] || { echo "No such file: sources/$FILE" >&2; exit 1; }

tofu() {
    docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp \
        --env-file "$TOFU_DIR/.env" "${TOFU_ENV[@]}" \
        -v "$TOFU_DIR:/w" -w /w "$TOFU_IMAGE" "$@"
}

# Change only the database's allowlist. The override wins over whatever
# ops/tofu/.env says, and the plan is targeted so nothing else can ride along.
set_allowlist() {
    TOFU_ENV=(-e "TF_VAR_db_admin_cidrs=$1")
    tofu plan -no-color -input=false -target=render_postgres.main -out=allowlist.tfplan \
        | grep -E '^Plan:|No changes' || true
    tofu apply -no-color -input=false allowlist.tfplan | grep -E '^Apply complete' || true
    rm -f "$TOFU_DIR/allowlist.tfplan"
}

manage() {
    (cd "$ROOT/dev" && docker compose run --rm -T \
        -e RUN_MIGRATIONS=0 -e DATABASE_URL="$DATABASE_URL" \
        api python manage.py "$@")
}

IP=$(curl -fsS https://api.ipify.org)
echo "==> Opening the production database to $IP"
set_allowlist "[\"$IP/32\"]"
trap 'echo "==> Closing the production database"; set_allowlist "[]"' EXIT

TOFU_ENV=()
DATABASE_URL=$(tofu output -raw database_external_url)
export DATABASE_URL

echo "==> Waiting for the database to accept this machine"
for attempt in $(seq 1 20); do
    if manage check --database default >/dev/null 2>&1; then
        break
    fi
    [ "$attempt" -lt 20 ] || { echo "The database never accepted the connection." >&2; exit 1; }
    sleep 6
done

echo "==> ingest_source $FILE as '$SLUG'"
manage ingest_source "/sources/$FILE" --slug "$SLUG" "$@"

echo "==> verify_anchors $SLUG"
manage verify_anchors "$SLUG"

echo "==> embed_source $SLUG"
manage embed_source "$SLUG"

echo "==> Done. Check: curl -s https://groundsource-api.onrender.com/sources"
