#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p evidence
.venv/bin/cyclonedx-py requirements requirements.txt --output-reproducible --of JSON -o evidence/sbom-python.json
npm sbom --prefix frontend --sbom-format cyclonedx --package-lock-only --omit=dev > evidence/sbom-frontend.json
