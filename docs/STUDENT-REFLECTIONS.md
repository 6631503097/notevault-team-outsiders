# Team Outsiders — student review and reflection worksheet

Verified technical facts are provided below. Personal reflection, contribution, and attestation fields must be completed by the named student after reviewing the code and reproducing evidence. Nobody may sign or answer for another member.

## Shared technical facts to understand

- F-02 is fixed by owner-scoping object queries; UI checks alone cannot enforce API authorization.
- Bound SQL parameters stop syntax injection but do not replace authorization.
- F-05 removes shell execution because export does not require a command interpreter.
- Sessions use random opaque tokens, stored hashes, expiry, rotation, and logout revocation.
- Authenticated writes use JSON/custom-header/session-bound CSRF and origin controls.
- The pipeline verifies configured tests/gates on a specific commit; it does not prove absence of all vulnerabilities.
- The SBOM inventories dependencies. The local Cosign signature proves artifact integrity against the local public key, not independent student identity or a formal SLSA level.
- Node2Shell is addressed by the Node 24.22.1 build pin and absence of Node in production. PHP2Shell is not applicable because there is no PHP surface.
- Priority residual risks include MFA/recovery, encrypted tested backups, centralized monitoring, immutable audit logs, and identity-backed signing.

## Zaw Win Htut — 6631503101

- Verified GitHub username: zawwinhtutdev
- Verified Git email: 156650937+zawwinhtutdev@users.noreply.github.com
- Review date/time/timezone: 2026-11-05, Asia/Bangkok (+07)
- Finding/fix personally reproduced: F-02 — broken object-level authorization (CWE-639), before on `lab/original`, after on `backend/app.py`; plus the DFD/STRIDE review of `docs/THREAT-MODEL.md`
- Exact command or browser action: `.lab-venv/bin/python scripts/reproduce_baseline.py` (before) and `PYTHONPATH=. .venv/bin/pytest -q tests/test_security.py::test_f02_owner_isolation_and_mass_assignment` (after); both against an isolated test client, no listener
- Evidence filename/link: `docs/REVIEW-ZAW-F02.md`; `evidence/f02-before-zaw-2026-11-05.png`; `evidence/f02-after-zaw-2026-11-05.png`
- Result observed in my own words: Before the fix, logging in as alice and requesting note 3 returned HTTP 200 with `owner=admin` and the team marker in the body — an ordinary account read an administrator's note just by knowing its number. After the fix the same read, and the matching write, both return 404, and the regression test passes. The URL did not change; the query now also demands that the row belong to the caller.
- Why the fix addresses the root cause: The original query filtered on the object ID alone, so authorization was never part of the data access. Adding `AND owner_id=?` means a foreign ID matches no row at all — nothing to leak even if a later check is forgotten — and the owner on create comes from the session rather than the request body, so it cannot be mass-assigned.
- One limitation/residual risk I identified: The owner predicate is hand-written in six places and nothing enforces it centrally. A seventh notes endpoint added with only `WHERE id=?` would reopen F-02 and no existing test would fail, so today the guarantee is "fixed at the known sites", not "enforced by construction"; a shared `note_for_user()` helper or an authorization test matrix is the missing piece.
- My actual contribution to review/demo/submission: Re-checked every DFD/STRIDE claim against the code (loopback binding, `foreign_keys=ON`, session expiry and revocation, login throttle, CSV formula guard, audit scoping, HTTPS/`COOKIE_SECURE` on the live deploy), reproduced F-02 before and after, wrote `docs/REVIEW-ZAW-F02.md`, captured the stamped evidence, and added the week-6 log row. Demo segment: F-02 attack → root cause → fix → retest.
- What I learned or would do differently: A passing "authorization" control is easy to believe and hard to prove — the useful question was not "is there a check?" but "where is the ownership condition, and what happens to every other query that forgets it?". Next time I would write the authorization test matrix before adding endpoints, and I would read `compose.yaml` against `deploy/README.md` earlier: `COOKIE_SECURE: "false"` is right for loopback and wrong if copied to production.
- I reviewed and understand the AI-assisted material — **yes/no** *(answer before merge)*
- I confirm these are actions I personally performed — **yes/no**
- Name/date:

## Wanna San — 6631503097

- Verified GitHub username:
- Verified Git email:
- Review date/time/timezone:
- Finding/fix personally reproduced:
- Exact command or browser action:
- Evidence filename/link:
- Result observed in my own words:
- Why the fix addresses the root cause:
- One limitation/residual risk I identified:
- My actual contribution to review/demo/submission:
- What I learned or would do differently:
- I reviewed and understand the AI-assisted material — **yes/no**
- I confirm these are actions I personally performed — **yes/no**
- Name/date:

## Myo Zin Thant — 6631503076

- Verified GitHub username: myo-zin-thant18
- Verified Git email: 6631503076@lamduan.mfu.ac.th
- Review date/time/timezone: 2026-11-05 23:20 Asia/Bangkok (UTC+7)
- Finding/fix personally reproduced: F-07 — forgeable sessions signed with a source-code secret (CWE-321 / CWE-613, A07:2025 Authentication Failures)
- Exact command or browser action: docker run --rm -v "$PWD":/app -w /app python:3.11 bash -c "pip install -q -r lab/original/requirements.txt itsdangerous==2.0.1 MarkupSafe==2.0.1 && python scripts/reproduce_baseline.py" ; then read finding F-07 in evidence/baseline.json
- Evidence filename/link: evidence/baseline.json (finding F-07, team marker 3d821afbe8a0) and evidence/wk6-f07-myo.png ; GET /admin → 200
- Result observed in my own words: I signed a session token with the app's hard-coded SECRET and the claim sub=admin, set it as my cookie, and requested /admin. The server accepted the forged token and returned 200 with the full user list, including the admin account's password hash — so I became admin without knowing any password.
- Why the fix addresses the root cause: the remediation replaces the source-secret JWT with random, opaque, server-stored sessions that expire and can be revoked on logout. There is no secret in the code to forge, and the server (not the token's signature) decides which sessions are valid.
- One limitation/residual risk I identified: opaque server sessions still depend on the confidentiality of the host and database — anyone who can read the session store or the database (for example the operator, or after a host compromise) can still hijack a session; the app also has no MFA or account-recovery control.
- My actual contribution to review/demo/submission: I personally reproduced F-07 against the isolated baseline harness, captured stamped evidence (evidence/wk6-f07-myo.png), recorded the run in docs/WEEKLY-LOG.md, and wrote this review on branch review/myo-f07.
- What I learned or would do differently: I learned why a secret committed in source code is effectively public and cannot authenticate anyone, and that session validity should be decided server-side rather than by a signature anyone can recompute.
- I reviewed and understand the AI-assisted material — **yes**
- I confirm these are actions I personally performed — **yes**
- Name/date: Myo Zin Thant — 2026-11-05

## Team completion

- Final team-owned repository URL:
- All collaborator invitations accepted — **yes/no**
- Instructor access verified — **yes/no**
- Shared AI scaffold accepted by instructor — **yes/no/pending**
- Demo URL tested while signed out:
- All three genuine review commits/PRs completed — **yes/no**
- Private peer ratings submitted — **yes/no**
- Final PDF rebuilt and visually reviewed — **yes/no**
- Portal receipt saved — **yes/no**

Do not write private submission codes or completed peer-rating explanations in this file.
