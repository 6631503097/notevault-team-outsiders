#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p evidence
.venv/bin/cyclonedx-py requirements requirements.txt --output-reproducible --of JSON -o evidence/sbom-python.json
npm sbom --prefix frontend --sbom-format cyclonedx --package-lock-only > evidence/sbom-frontend.json

.venv/bin/python - <<'PYVERIFY'
import json
sbom=json.load(open('evidence/sbom-frontend.json'))
names={c['name'] for c in sbom['components']}
assert {'react','react-dom','scheduler','lucide-react'} <= names, 'Incomplete frontend SBOM'
PYVERIFY
