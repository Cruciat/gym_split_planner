#!/bin/sh
# Avvio del container (ADR 0009): migrazioni, dati iniziali al primo avvio, poi il server.
# Se una migrazione fallisce il container si ferma, invece di servire un database a metà.
set -eu

python -m gym_split_planner migrate
python -m gym_split_planner seed

exec uvicorn gym_split_planner.app:create_app \
    --factory \
    --host 0.0.0.0 \
    --port 8000 \
    --proxy-headers \
    --forwarded-allow-ips "*" \
    --no-server-header
