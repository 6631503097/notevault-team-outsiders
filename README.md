# NoteVault - Team Outsiders / Fieldnotes

A complete React + TypeScript + Vite frontend and Flask API, evolved from the provided course NoteVault target. Local SQLite persistence, private notes, account creation/login, editing, search, collections, pinning, archive, reversible removal, JSON/CSV/text export, team directory, account activity and an admin user directory are implemented.

## Open or run

Audited deployment: the local loopback app and the team-owned CI container. The external URL recorded in team.json was inherited; only its health/config endpoints were checked here. Deployment ownership and reverse-proxy configuration are not claimed. See docs/EVIDENCE-PROVENANCE-AUDIT.md.

Open **http://127.0.0.1:8081**. Start from this directory with:

```sh
docker compose up --build -d --wait
```

The app listens only on this computer. Seeded **local classroom demo** credentials: `alice / alicepw` and `admin / admin123`. Accounts are seeded only for a new database with `DEMO_MODE=true`. Normal registrations require a 12-128 character password and can never select an admin role.

Alternatively, install Python 3.12+ and Node 24+, then run `./scripts/start.sh`. Do not start the local and Docker servers on the same port simultaneously. `docker compose stop` stops without deleting data; `docker compose start` starts the same data again. `docker compose down` also preserves the named volume; **do not add `-v` unless you deliberately want to erase it**.

## Team

- Zaw Win Htut - 6631503101
- Wanna San - 6631503097
- Myo Zin Thant - 6631503076

`team.json` is the source of team identity. The database records the TEAM_ID at initialization and refuses to start with a different team name. This team uses its own database, volume, port, session-cookie name and marker.

## Verification

```sh
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python --require-hashes -r requirements-dev.txt
npm ci --prefix frontend
# Install official gitleaks and cosign CLIs for security/release verification.
./scripts/verify.sh
./scripts/sbom.sh
.venv/bin/python scripts/package_release.py
.venv/bin/python scripts/sign_local.py
.venv/bin/python scripts/container_check.py
```

`docs/BASELINE.md` documents safe reproduction of the original course vulnerabilities without starting a vulnerable public server. `evidence/` contains both inherited historical outputs and subsequent checks; the corrected report uses only the source ledger in evidence/audit/provenance.json; it is not a substitute for student identity-stamped screenshots or independent reproduction.

## Rubric and handoff

- `docs/REPORT.md` - report draft following the provided headings, verified findings and fix references.
- `docs/THREAT-MODEL.md` and `docs/dfd.svg` - DFD, boundaries, STRIDE and ranked risks.
- `docs/DEMO.md` - Week 16/19 walkthrough and viva preparation.
- `docs/WEEKLY-LOG.md` - real investigation and contribution tracking.
- `docs/AI-DISCLOSURE.md` - shared AI-assisted code disclosure for both teams.
- `docs/SEVEN-PHASE-TEAM-HANDOFF.md` - identity-safe repository migration and rubric completion procedure.
- `docs/STUDENT-REFLECTIONS.md` - per-member technical review, reflection, and attestation worksheet.
- `docs/PEER-FEEDBACK-TEMPLATE.md` - private Full/Most/Some/Little peer-rating form.
- `docs/MACHINE-EXECUTION-PROMPT.md` - location and usage boundary for the packaged copy/paste machine prompt.
- `.github/workflows/security.yml` - tests, SAST, SCA, secret scanning, container checks and signed tag releases.
- `release/` - actual locally signed release, verification bundle, public key and digests; never distribute `.keys/`.

All Team Outsiders members must review and understand the shared implementation, independently reproduce findings, capture required screenshots, keep real contribution histories, and confirm acceptance of shared scaffolding with the instructor. The team-owned private repository is https://github.com/6631503097/notevault-team-outsiders. The disclosed history is preserved. All three members have access; instructor access remains pending. Peer feedback, completed personal reflections, the recorded demo and portal submission remain team actions.

## Scope and limits

The inherited external-deployment narrative is outside the verified scope. Local container protections and CI checks are recorded separately. Demo accounts are intentionally visible only in local demo mode. Backups, monitoring, MFA/recovery and administrator provisioning remain operational limits. Notes are private per account, not shared automatically among teammates. Student IDs are shown only after sign-in, except the non-secret team name and marker.

The single SQLite database supports modest course use; auth throttles are stored there and survive restarts. A user can hold at most 1,000 notes, including removed notes; administrators see up to 500 accounts. Audit records are operational history, not tamper-proof evidence. There is no password recovery, MFA, email service or file-upload feature. Restarts never reset existing data. Archive/remove are reversible; no destructive delete endpoint is exposed.

The original target remains unchanged in `lab/original`, excluded from the runtime image and release. Its initial Git commit and later remediation commits honestly record this session; no past weekly work or student authorship is fabricated.

## Regenerate the report draft

```sh
uv pip install --python .venv/bin/python --require-hashes -r requirements-report.txt
.venv/bin/python scripts/build_report.py
```

Run the evidence scripts first. The report generator reads actual local evidence and Git fix references. Review the generated PDF visually before submitting it; it remains a draft until the team completes its missing evidence and personal sections.
