#!/usr/bin/env sh
set -eu
[ $# -eq 1 ] || { echo "Uso: $0 archivo.sql"; exit 1; }
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$1"
