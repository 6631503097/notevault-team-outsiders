#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p evidence
.venv/bin/python -m pytest -q tests --junitxml=evidence/regression.xml
npm run test --prefix frontend
npm run build --prefix frontend
.venv/bin/python scripts/security_gate.py
.venv/bin/python scripts/prove_gate.py
