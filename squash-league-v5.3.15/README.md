# Squash League V5.3.15

Base desplegable para gestionar una liga de squash: API FastAPI, shell PWA y servicios Docker.

## Inicio rápido

1. Copia `.env.example` a `.env` y cambia las claves.
2. Ejecuta `docker compose up -d --build`.
3. Abre `http://localhost`; la API responde en `/api/health` y se documenta en `/docs`.

## Scripts

`install.sh`, `update.sh`, `backup.sh`, `restore.sh`, `healthcheck.sh` y `create-admin.sh` cubren la operación básica.
