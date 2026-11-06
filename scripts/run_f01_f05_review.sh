#!/usr/bin/env bash
# Caller must supply the operator label. It is a self-report, not identity proof.
set -euo pipefail
if [[ $# -ne 2 || "$1" != '--operator-label' ]]; then
  echo 'Usage: bash scripts/run_f01_f05_review.sh --operator-label "YOUR ACTUAL OPERATOR / ASSISTANCE DESCRIPTION"' >&2
  exit 2
fi
review_operator="$2"
cd -- "$(dirname -- "$0")/.."
review_python="${REVIEW_PYTHON:-$PWD/.venv/bin/python}"
review_lab_python="${REVIEW_LAB_PYTHON:-$PWD/.lab-venv/bin/python}"
if [[ ! -x "$review_python" && -x /tmp/outsiders-report-env/bin/python ]]; then
  review_python=/tmp/outsiders-report-env/bin/python
fi
if [[ ! -x "$review_lab_python" && -x /tmp/outsiders-lab-review-env/bin/python ]]; then
  review_lab_python=/tmp/outsiders-lab-review-env/bin/python
fi
if [[ ! -x "$review_python" || ! -x "$review_lab_python" ]]; then
  echo 'Set up the README/BASELINE environments, or set REVIEW_PYTHON and REVIEW_LAB_PYTHON to your installed environments.' >&2
  exit 2
fi
mkdir -p evidence/review-wanna-f01-f05
printf 'Prepared for Wanna San | 6631503097 | Team Outsiders\nOperator label (self-reported): %s\n' "$review_operator"
date '+%Y-%m-%d %H:%M:%S %z'
"$review_lab_python" --version
"$review_python" --version
printf '\nBASELINE - isolated client, harmless probes only\n'
set -x
"$review_lab_python" scripts/capture_f01_f05.py --mode baseline --operator-label "$review_operator" --summary | tee evidence/review-wanna-f01-f05/baseline.log
set +x
printf '\nPATCHED - rejected attacks and legitimate behavior\n'
set -x
PYTHONPATH=. "$review_python" scripts/capture_f01_f05.py --mode patched --operator-label "$review_operator" --summary | tee evidence/review-wanna-f01-f05/patched.log
PYTHONPATH=. "$review_python" -m pytest -q tests/test_security.py -k 'f01 or f05 or legitimate_note_lifecycle_and_exports' --junitxml=evidence/review-wanna-f01-f05/regression.xml | tee evidence/review-wanna-f01-f05/regression.log
"$review_python" scripts/capture_f01_f05.py --refresh-manifest
set +x
printf '\nExecution finished. Inspect the actual results before making a personal attestation.\nSave your own terminal screenshots in evidence/review-wanna-f01-f05/.\n'
