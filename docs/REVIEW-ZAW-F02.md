# Review — DFD/STRIDE and F-02 owner-boundary (Zaw Win Htut, 6631503101)

Reviewer: **Zaw Win Htut — 6631503101**
Team marker: `3d821afbe8a0` · Repository: `6631503097/notevault-team-outsiders` @ `remediation`
Review date/time/timezone: **2026-11-05, Asia/Bangkok (+07)**
Scope (per `docs/SEVEN-PHASE-TEAM-HANDOFF.md` Phase 2): the data-flow diagram and STRIDE table in
`docs/THREAT-MODEL.md`, and finding **F-02 — broken object-level authorization**.

AI assistance: the commands below were run with an AI assistant driving the shell on my machine; the
review conclusions, the residual-risk judgement and the reflection are my own. Evidence captures are
from my own session and carry my name/ID, the real timestamp and the team marker. This is disclosed
in line with `docs/AI-DISCLOSURE.md`.

---

## 1. Threat-model review — does the DFD/STRIDE match the code?

I checked each claim in `docs/THREAT-MODEL.md` against the source rather than accepting the prose.
Every boundary claim I tested held, with the locations below.

| Claim in the threat model | Where I verified it | Verdict |
|---|---|---|
| **TB2** "The local preview is loopback-only" | `compose.yaml:6` publishes `127.0.0.1:8081:8080`; `scripts/start.sh:12` binds gunicorn to `127.0.0.1:$PORT` | Confirmed — no wildcard bind in either path |
| **TB3** persistent storage is SQLite with foreign keys | `backend/app.py:49` `PRAGMA foreign_keys=ON`; `Dockerfile` sets `DATABASE=/data/notevault.db`; `compose.yaml` mounts named volume `notes:/data` with `read_only: true` for the rest of the rootfs | Confirmed — the only writable path is the volume, so the container really is read-only apart from `/data` and `/tmp` |
| Browser→API uses opaque sessions | `backend/app.py:125` creates `sessions(token_hash, csrf, expires_at)`; `:160` requires `expires_at>?`; `:269` revokes by deleting the row | Confirmed — no signed/self-describing cookie; expiry is server-side |
| Login/registration throttle | `backend/app.py` `attempts` table, 900-second window, `429` at `:225` and `:249` | Confirmed |
| Export is owner-scoped, allowlisted, and neutralises CSV formulas | `backend/app.py:341` (`/api/export`), `:357` prefixes `'` when a cell starts with `= + - @ \t \r \n`, `:363` sends `Content-Disposition: attachment` | Confirmed — the formula guard is real code, not a claim |
| Audit history records actor/action/target/time | `backend/app.py:62` `audit()` writes `(user_id, action, target, created_at)`; `:372` `/api/activity` returns **only** `WHERE user_id=?` | Confirmed — and the endpoint does not leak other users' rows, so the "repudiation" control does not create a disclosure |
| **TB4** release integrity (SBOM, signature, gated CI) | `.github/workflows/security.yml`, `evidence/hosted-ci.json`, `docs/REPORT.md` release section | Confirmed as documented; see the residual risk in §4 |
| Live service is HTTPS with the same app behind Nginx | `deploy/README.md` sets `COOKIE_SECURE=true`, `TRUSTED_HOSTS=outsiders.3-0-126-159.nip.io`; `deploy/nginx-site.conf:15-20` listens `443 ssl` with Certbot certs | Confirmed — and this matters, because `compose.yaml` sets `COOKIE_SECURE: "false"` for the loopback preview only |

**Conclusion:** the DFD's four trust boundaries (browser, app process, SQLite storage, build/release)
match the code, and the STRIDE rows are backed by real controls rather than aspirational ones. The
one thing I would change is presentation, not substance: `compose.yaml`'s `COOKIE_SECURE: "false"` is
correct for `127.0.0.1` but it is also the line someone would copy when deploying without reading
`deploy/README.md`. A comment on that line pointing at the production environment file would remove
the footgun.

---

## 2. F-02 — the finding, reproduced before and after

**Finding (from `docs/REPORT.md`):** F-02 — broken object-level authorization, **CWE-639**,
A01:2025 Broken Access Control / API1:2023 BOLA, severity High, original location
`lab/original/app.py:166`, request `GET /api/notes/3`.
**Root cause:** the original lookup filtered on the object ID only — `SELECT ... FROM notes WHERE id=?` —
so any authenticated user could read any note by walking the sequential IDs.

### Before (unmodified starter, isolated test client, no listener)

```sh
.lab-venv/bin/python scripts/reproduce_baseline.py
```

```
"team": "Team Outsiders", "marker": "3d821afbe8a0", "probes_passed": 10
finding : F-02 - Alice reads the administrator build marker
request : GET /api/notes/3 as alice  ->  HTTP 200
response: {"body":"team=Team Outsiders marker=3d821afbe8a0","id":3,"owner":"admin","title":"build-tag"}
```

Alice, an ordinary user, receives note `id=3` whose `owner` is `admin`, including the team build
marker. That is the vulnerability: authentication succeeded, authorization did not exist.

![F-02 before](f02-before-zaw-2026-11-05.png)

*`evidence/f02-before-zaw-2026-11-05.png` — my own session, stamped with name/ID, team marker and timestamp.*

### After (hardened `backend/app.py`)

```sh
PYTHONPATH=. .venv/bin/pytest -q tests/test_security.py::test_f02_owner_isolation_and_mass_assignment
# 1 passed in 1.98s
```

The regression test asserts the three things that matter together:

1. `GET /api/notes/{foreign_id}` → **404** (test line ~53);
2. `PUT /api/notes/{foreign_id}` → **404** (a write, not just a read);
3. a client-supplied `owner_id` on create is **ignored** — the created note's owner is the
   authenticated user, so the fix is not bypassable by mass assignment.

![F-02 after](f02-after-zaw-2026-11-05.png)

*`evidence/f02-after-zaw-2026-11-05.png` — the passing test plus the predicates it depends on.*

---

## 3. Why the fix addresses the root cause

The fix moves authorization **into the query** instead of checking it after a fetch:

```diff
- SELECT id,owner,title,body FROM notes WHERE id = ?
+ SELECT ... FROM notes WHERE id=? AND owner_id=?
```

Applied at every read and write path (`backend/app.py:282` list/search, `:307` quota count, `:320`
read, `:331` update, `:339` post-update read, `:347` export), and paired with a server-supplied owner
on insert (`:299`, `:311`). Two consequences follow that a "check after fetch" fix would not give:

- A foreign ID matches **zero rows**, so there is no object to leak even if a later change forgets to
  check a variable — the predicate is part of the data access, not a separate decision.
- Returning **404 rather than 403** keeps the response uniform for "does not exist" and "not yours",
  which avoids turning the endpoint into an object-existence oracle. The cost is a slightly less
  helpful developer error, which I think is the right trade here.

---

## 4. Residual risk I identified

**Authorization is per-query, not systemic.** The owner predicate is hand-written in six places
(`:282, :307, :320, :331, :339, :347`). Nothing in the codebase prevents a *seventh* endpoint from
being added with `WHERE id=?` alone, and no test would fail until someone writes a test for it. The
current protection is correct but is a **convention enforced by review**, not a property enforced by
construction.

Concretely, the next endpoint that touches notes must either reuse a shared helper (a single
`note_for_user(nid)` that always applies both predicates) or the codebase needs an authorization test
matrix that fails when a new route skips the owner column. Until one of those exists, the honest
statement is "F-02 is fixed at the six known sites" rather than "object-level authorization is
enforced".

Secondary, smaller: there is no per-object sharing model, so if collaboration is ever added the
predicate has to become a relationship check (owner *or* share) — at which point five of the six call
sites change at once. That is the same fragility from a different direction, and it is worth writing
down before the feature is requested.

---

## 5. Verification log (what I actually ran)

| Step | Command | Result |
|---|---|---|
| 1 | `.lab-venv/bin/python scripts/reproduce_baseline.py` | 10/10 probes passed; F-02 = HTTP 200, `owner=admin`, marker present |
| 2 | `PYTHONPATH=. .venv/bin/pytest -q tests/test_security.py::test_f02_owner_isolation_and_mass_assignment` | `1 passed in 1.98s` |
| 3 | `grep -n 'WHERE id=? AND owner_id=?' backend/app.py` | 6 call sites, listed in §4 |
| 4 | `grep -n 'INSERT INTO notes' backend/app.py` | 3 inserts; owner comes from the session, not the request body |
| 5 | `grep -n 'PRAGMA foreign_keys' backend/app.py` etc. | threat-model claims in §1 confirmed at the cited lines |

I did not run the historical Compose file, did not expose the vulnerable app on any interface, and
used only the isolated test client described in `docs/BASELINE.md`.
