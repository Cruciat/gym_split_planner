#!/usr/bin/env bash
# Server dei test end-to-end: l'app compilata (frontend/dist) servita dal backend, su
# un database nuovo con i dati iniziali. Lo avvia e lo ferma Playwright (webServer).
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
data="$(mktemp -d)"
trap 'rm -rf "$data"' EXIT

cd "$here/../../backend"
export GSP_DATABASE_URL="sqlite:///$data/e2e.db"
export GSP_STATIC_DIR="$here/../dist"
export GSP_BACKUP_ENABLED=false

uv run python -m gym_split_planner migrate
uv run python -m gym_split_planner seed
uv run uvicorn gym_split_planner.app:create_app --factory --host 127.0.0.1 --port "${E2E_PORT:-8799}"
