#!/usr/bin/env sh
set -eu
[ $# -eq 2 ] || { echo "Uso: $0 email contraseña"; exit 1; }
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "INSERT INTO users (email, role) VALUES ('$1', 'admin') ON CONFLICT (email) DO UPDATE SET role='admin';"
echo "Administrador preparado: $1"
