#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then python3 -m venv .venv; fi
.venv/bin/python -m ensurepip --upgrade
.venv/bin/python -m pip install --require-hashes -r requirements.txt
npm ci --prefix frontend
npm run build --prefix frontend
PORT="$(.venv/bin/python -c 'import json; print(json.load(open("team.json"))["port"])')"
mkdir -p instance
export DEMO_MODE="${DEMO_MODE:-true}"
exec .venv/bin/gunicorn 'backend.app:create_app()' --bind "127.0.0.1:$PORT" --workers 1 --threads 4 --control-socket instance/gunicorn.ctl --access-logfile -
