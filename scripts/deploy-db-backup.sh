#!/usr/bin/env bash
# Run from the production compose directory before applying pending migrations.
# Credentials stay in a private temporary file on the server, never in CI output.
set -euo pipefail
umask 077

BACKUP_DIR=${1:?Usage: deploy-db-backup.sh BACKUP_DIR REVISION}
REVISION=${2:?Usage: deploy-db-backup.sh BACKUP_DIR REVISION}
if ! [[ "$REVISION" =~ ^[0-9a-fA-F]{7,40}$ ]]; then
  echo "Backup revision must be a Git commit hash." >&2
  exit 1
fi
mkdir -p -- "$BACKUP_DIR"
chmod 700 -- "$BACKUP_DIR"
BACKUP_DIR=$(cd "$BACKUP_DIR" && pwd -P)
PG_ENV_FILE=$(mktemp "$BACKUP_DIR/.pg-backup-env.XXXXXX")
trap 'rm -f -- "$PG_ENV_FILE"' EXIT

# Read the running application's actual connection settings without exposing them.
# This command only prints validated env-file lines; do not enable shell tracing.
docker compose exec -T api python -c '
import contextlib
import io
from django.conf import settings
with contextlib.redirect_stdout(io.StringIO()):
    database = settings.DATABASES["default"]
if database["ENGINE"] != "django.db.backends.postgresql":
    raise ValueError("This backup script requires PostgreSQL.")
values = {
    "PGHOST": database.get("HOST") or "localhost",
    "PGPORT": database.get("PORT") or "5432",
    "PGDATABASE": database["NAME"],
    "PGUSER": database.get("USER") or "postgres",
    "PGPASSWORD": database.get("PASSWORD") or "",
}
for key, value in values.items():
    value = str(value)
    if "\n" in value or "\r" in value:
        raise ValueError("Database settings cannot contain newlines in a backup env file.")
    print(f"{key}={value}")
' > "$PG_ENV_FILE"
chmod 600 -- "$PG_ENV_FILE"

PG_MAJOR=$(docker compose exec -T api python -c '
from django.db import connection
print("PG_MAJOR=" + str(connection.pg_version // 10000))
' | sed -n 's/^PG_MAJOR=//p')
if ! [[ "$PG_MAJOR" =~ ^[1-9][0-9]*$ ]]; then
  echo "Could not determine PostgreSQL server major version; migration is blocked." >&2
  exit 1
fi

CLIENT_IMAGE="postgres:${PG_MAJOR}-alpine"
BACKUP_NAME="pre-migrate-$(date -u +%Y%m%dT%H%M%SZ)-${REVISION}.dump"
CLIENT_USER="$(id -u):$(id -g)"

# The database is external to this compose stack. Match the server major and
# preserve host.docker.internal for connections to the Docker host.
docker run --rm --network host --add-host host.docker.internal:host-gateway \
  --user "$CLIENT_USER" --env-file "$PG_ENV_FILE" \
  --volume "$BACKUP_DIR:/backup" "$CLIENT_IMAGE" \
  pg_dump --format=custom --file="/backup/${BACKUP_NAME}.partial"
chmod 600 -- "$BACKUP_DIR/${BACKUP_NAME}.partial"
docker run --rm --network none --user "$CLIENT_USER" \
  --volume "$BACKUP_DIR:/backup:ro" "$CLIENT_IMAGE" \
  pg_restore --list "/backup/${BACKUP_NAME}.partial" > /dev/null
mv -- "$BACKUP_DIR/${BACKUP_NAME}.partial" "$BACKUP_DIR/$BACKUP_NAME"
echo "Verified pre-migration backup: $BACKUP_DIR/$BACKUP_NAME"
