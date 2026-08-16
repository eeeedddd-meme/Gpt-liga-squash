#!/usr/bin/env sh
set -eu
mkdir -p backups
docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "backups/squash-$(date +%Y%m%d-%H%M%S).sql"
