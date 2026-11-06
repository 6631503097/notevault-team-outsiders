# Term Project Report - Secure Build

## Cover

| Field | Value |
|---|---|
| Team name | Team Outsiders |
| Members (name + ID) | Zaw Win Htut 6631503101; Wanna San 6631503097; Myo Zin Thant 6631503076 |
| Target application | Provided NoteVault, upgraded to Fieldnotes |
| Repository URL | https://github.com/6631503097/notevault-team-outsiders (private; nutthakorn7 invited with write access; acceptance pending) |
| Audited application | Local loopback app at http://127.0.0.1:8081; no external deployment ownership claimed |
| Evidence review date | 2026-11-06 (Asia/Bangkok) |
| Recorded demo URL | https://drive.google.com/file/d/1dyuYW3Ln3t05w3GKuYHs74RNAFCseIBZ/view |
| Assessment baseline marker | 3d821afbe8a0 |
| Status | Submission report; instructor invitation sent; acceptance and individual documentation verification pending |

## AI-tool usage disclosure

OpenAI Codex assisted with requirements review, implementation, tests, local vulnerability reproduction, build/security tooling and this report. Both teams received shared AI-assisted code in the same session. Different team names and markers do not make shared source independently authored. See docs/AI-DISCLOSURE.md. Students must disclose this assistance, independently reproduce and understand results, and confirm acceptance of the shared scaffolding with the instructor. No student authorship, weekly history or personal reflection is fabricated. The hosted CI result is linked to its GitHub run and recorded in evidence/audit/hosted-ci.json.

## 1. Executive Summary

Team Outsiders uses NoteVault as a local private notebook with account registration, sessions, owner-scoped notes and exports. Its Fieldnotes interface organizes notes into Fieldwork, Research, Personal. The assessment verified ten harmless baseline probes grouped into eight findings: two Critical, four High, and two Medium, using qualitative severity. The critical risks are shell injection and session forgery; authorization, SQL construction, interpreted content and password handling add further risk.

The inherited, disclosed React/TypeScript client and Flask API remove the demonstrated mechanisms, retain legitimate application behavior and add persistent storage, conflict detection and reversible note removal. The security regression suite and frontend tests exercise both successful use and rejected attacks. Original source and actual probe outputs are retained. The report does not claim independent student authorship or invent personal contributions. The hosted Actions run is recorded as machine-generated evidence; the team supplied the recorded presentation link; each student must attest to their own review before upload.

## Verification at a glance

Evidence is drawn from the independent local execution journal and explicitly generated outputs of the recorded team-owned CI job. The inherited source is not claimed as new implementation work. It does not establish student review, instructor acceptance, demo completion or portal submission. See docs/TEAM-NEXT-STEPS.md.

| Control | Result | Evidence |
|---|---|---|
| Vulnerable baseline | 10 harmless probes reproduced across 8 findings | evidence/audit/baseline.json |
| Backend regression | 25 tests passed | evidence/audit/regression.xml |
| Frontend regression | 3 tests passed and production build completed | frontend/src/App.test.tsx; evidence/audit/frontend-build.log; evidence/audit/frontend-tests-attempt2.log |
| Dependency audit | 0 known Python vulnerabilities; 0 npm vulnerabilities | evidence/audit/ci/sca-python.json; evidence/audit/ci/sca-npm.json |
| Container gate | 0 HIGH/CRITICAL findings; hardened runtime controls verified | evidence/audit/ci/sca-container.json; evidence/audit/ci/container-check.json |
| Secret scan | 0 findings | evidence/audit/ci/secrets-history.json |
| Release integrity | Cosign verification passed; tampered copy rejected | evidence/audit/signature.log; evidence/audit/tamper-rejection.log |
| Hosted pipeline | Passed security job at https://github.com/6631503097/notevault-team-outsiders/actions/runs/42068311164 on 82d6f4a05bb2bf3c92fd5d5b19ba56bb8c5fec2f; tag-only signing skipped | evidence/audit/hosted-ci.json |

## 2. System Scope & Function

The application provides local account creation/sign-in, note creation/view/edit, literal search, collections, pin/archive/restore, CSV/JSON/text downloads, personal audit history, a protected team directory, and an administrator account listing without passwords. Notes remain private per user, even for administrators. The audited Team Outsiders configuration uses its own team identity, database, volume, cookie name and port. Other teams are outside this assessment.

The original assessment target is lab/original/app.py from course revision 6996818be46cfb3f26b9b9d88e7c95af7ae32176. It is excluded from runtime/release packaging. scripts/reproduce_baseline.py loads it in a separate old-dependency environment and temporary SQLite database; it does not start a listener. The assessment baseline retains marker 3d821afbe8a0. The marker verifies the test fixture configuration; it does not establish independent authorship or the origin of an inherited screenshot.

Data-flow diagram: docs/dfd.svg and docs/THREAT-MODEL.md. Trust boundaries separate the browser, Flask process, local database and build/release pipeline. The audited container is loopback-bound. External reverse-proxy configuration and deployment ownership have not been verified in this audit. Protected assets include private notes, password hashes, session tokens, audit records and release integrity. Real university services and real credentials are out of scope.

## 3. Threat Model - STRIDE (20 pts)

| Element or flow | STRIDE risks | Mitigation and residual risk |
|---|---|---|
| Browser to API | Spoofing, tampering, information disclosure, elevation | Opaque sessions, JSON + CSRF, owner predicates, escaping and CSP. HTTPS is required outside loopback. |
| Registration/login | Spoofing, denial of service, elevation | Server-selected role, scrypt, generic errors, persistent IP throttle. No MFA or recovery flow. |
| Notes API to SQLite | Tampering, information disclosure, elevation | Parameters, owner IDs, foreign keys, versions and input limits. A host/database operator can still read data. |
| Export to browser | Tampering, information disclosure | Owner-scoped serialization, format allowlist, attachment download and CSV formula protection. Downloaded files become the user’s responsibility. |
| Audit history | Repudiation, tampering | Record actor, action, object and timestamp. Local logs are not immutable or externally monitored. |
| Dependencies/build/release | Tampering, elevation, information disclosure | Lockfiles with hashes, pinned base images/actions, scan gates, SBOM and signatures. Trust still includes registries, build tools and signing-key custody. |

### Ranked top risks

| Rank | Threat | Likelihood x impact (1-5) | Before / mitigation |
|---|---|---|---|
| 1 | F-05 shell execution | 5 x 5 = 25 | Arbitrary commands; remove the shell completely. |
| 2 | F-07 session forgery | 5 x 5 = 25 | Impersonation; random, expiring, revocable server sessions. |
| 3 | F-01 injection | 5 x 4 = 20 | Query manipulation; bind all user values. |
| 4 | F-02/F-03 authorization | 5 x 4 = 20 | Cross-user data and roles; server-side authorization. |
| 5 | F-04 interpreted stored content | 4 x 5 = 20 | HTML/template injection; typed JSON and text rendering. |

Likelihood and impact are each ranked 1-5 to prioritize remediation. These are qualitative estimates, not formal CVSS calculations. Residual risk includes host compromise, database access by the operator, supply-chain trust and the explicitly enabled local demo accounts.

## 4. Vulnerability Findings (25 pts)

Run the steps in docs/BASELINE.md. Every probe is linked to the exact team marker and original-source digest in evidence/audit/baseline.json. Only temporary fake data is used.

### Finding F-01 - SQL injection in login and search

| Field | Value |
|---|---|
| CWE | CWE-89 |
| OWASP 2025 | A05:2025 Injection |
| Severity | High |
| Location | lab/original/app.py:128; login / search |
| Evidence | evidence/audit/baseline.json, finding F-01, team marker 3d821afbe8a0 |

Reproduction: Log in with username admin' -- and an incorrect password; the old route returns a session cookie. Separately, authenticate as Alice and search for ' OR 1=1 -- . The response includes the administrator’s team marker.

Impact: The attacker bypasses the credential check and can read notes across owner boundaries using the search query. The bypassed login’s subject is the supplied string; the evidence does not falsely claim that this SQLi alone yields a normal administrator subject.

Root cause: SQL strings interpolate username and search terms.

### Finding F-02 - Broken object-level authorization

| Field | Value |
|---|---|
| CWE | CWE-639 |
| OWASP 2025 | A01:2025 Broken Access Control / API1:2023 BOLA |
| Severity | High |
| Location | lab/original/app.py:166; GET /api/notes/3 |
| Evidence | evidence/audit/baseline.json, finding F-02, team marker 3d821afbe8a0 |

Reproduction: Authenticate as Alice in the original app and request /api/notes/3. The JSON owner is admin, and the body contains this team’s marker.

Impact: Any signed-in user can enumerate private notes belonging to other accounts.

Root cause: The original lookup checks only the object ID.

### Finding F-03 - Role escalation during registration

| Field | Value |
|---|---|
| CWE | CWE-269 / CWE-915 |
| OWASP 2025 | A01:2025 Broken Access Control |
| Severity | High |
| Location | lab/original/app.py:114; POST /register |
| Evidence | evidence/audit/baseline.json, finding F-03, team marker 3d821afbe8a0 |

Reproduction: Register probe_user with role=admin, log in, then request /admin. The original app grants administrator access.

Impact: An untrusted registrant receives a privileged role and can list accounts and password digests.

Root cause: Registration trusts the client-supplied role.

### Finding F-04 - Stored HTML injection and server template evaluation

| Field | Value |
|---|---|
| CWE | CWE-79 / CWE-1336 |
| OWASP 2025 | A05:2025 Injection |
| Severity | High |
| Location | lab/original/app.py:181; POST /notes; GET /; GET /search |
| Evidence | evidence/audit/baseline.json, finding F-04, team marker 3d821afbe8a0 |

Reproduction: Save <img src=x onerror=alert(1)> and retrieve the home page: the HTML appears unescaped. Save {{7*7}} and search for 7*7: the original response renders Template probe: 49.

Impact: Stored content is interpreted as HTML or a template. The harmless expression proves server-side template evaluation. A browser alert or arbitrary-code-execution screenshot is not claimed.

Root cause: The original home marks concatenated HTML safe; search concatenates untrusted data into template source.

### Finding F-05 - Shell command injection in export

| Field | Value |
|---|---|
| CWE | CWE-78 |
| OWASP 2025 | A05:2025 Injection |
| Severity | Critical |
| Location | lab/original/app.py:202; GET /export?fmt=... |
| Evidence | evidence/audit/baseline.json, finding F-05, team marker 3d821afbe8a0 |

Reproduction: As Alice, request fmt=txt; printf NV_SAFE_PROBE. The original response contains NV_SAFE_PROBE, proving that the additional harmless shell command ran.

Impact: An authenticated attacker controls a shell command executed as the application user. Only a harmless output marker was executed during verification.

Root cause: The export route concatenates fmt into a command passed with shell=True.

### Finding F-06 - Fast password digests and digest disclosure

| Field | Value |
|---|---|
| CWE | CWE-916 / CWE-200 |
| OWASP 2025 | A04:2025 Cryptographic Failures |
| Severity | Medium |
| Location | lab/original/app.py:117; users table; GET /admin |
| Evidence | evidence/audit/baseline.json, finding F-06, team marker 3d821afbe8a0 |

Reproduction: After reproducing role escalation, request /admin and compare the exposed administrator digest to the MD5 of the known sample password. Both are identical.

Impact: An account-table leak gives attackers unsalted fast password digests suitable for offline guessing. Severity rises when chained with F-03. No real account credential was tested.

Root cause: MD5 is used as an unsalted password digest, and the admin response includes that digest.

### Finding F-07 - Forgeable sessions signed with a source-code secret

| Field | Value |
|---|---|
| CWE | CWE-321 / CWE-613 |
| OWASP 2025 | A07:2025 Authentication Failures |
| Severity | Critical |
| Location | lab/original/app.py:23; session cookie; GET /admin |
| Evidence | evidence/audit/baseline.json, finding F-07, team marker 3d821afbe8a0 |

Reproduction: Use the known constant SECRET in the original source to sign an HS256 token with sub=admin, then request /admin with that cookie. The response is 200.

Impact: Anyone with the source secret can impersonate the administrator. This does not rely on or claim an alg=none bypass.

Root cause: A hard-coded JWT key is shared with all deployments, and tokens lack enforced expiry and server revocation.

### Finding F-08 - Missing request protection for state changes

| Field | Value |
|---|---|
| CWE | CWE-352 |
| OWASP 2025 | A01:2025 Broken Access Control |
| Severity | Medium |
| Location | lab/original/app.py:140; POST /notes; GET /logout |
| Evidence | evidence/audit/baseline.json, finding F-08, team marker 3d821afbe8a0 |

Reproduction: Send an authenticated form POST to /notes with Origin: https://attacker.invalid and no CSRF token. The old server accepts it. Browser exploitability depends on its cookie defaults and is not universally asserted.

Impact: The server does not distinguish legitimate state changes from attacker-origin requests carrying credentials; logout also mutates state on GET.

Root cause: No CSRF token or origin validation is required. Cookie attributes are weak.

## 5. Remediation (25 pts)

The original source is preserved rather than rewritten. The inherited application upgrade is broader than a minimal patch; each security change below is tied to the specific unsafe mechanism. All listed fixes were already present in the inherited AI-assisted remediation commit. This audit independently checks their behavior; it does not claim to have implemented them anew or attribute them to a student.

### Fix for F-01

Use bound SQL parameters, fetch the canonical user row, and verify its password hash. Search binds both owner ID and escaped literal search text.

```diff
- q = "SELECT * FROM users WHERE username = ..." % username
+ row = db().execute("SELECT * FROM users WHERE username=?", (name,)).fetchone()
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:253.

Proof: test_f01_sql_injection_login_and_search. See evidence/audit/regression.xml and frontend/src/App.test.tsx. These retained tests verify the rejected attack and relevant legitimate behavior. Every baseline behavior also retains its exact machine-generated request/response evidence in evidence/audit/baseline.json.

### Fix for F-02

Every read and write constrains both the note ID and authenticated owner ID. The server supplies ownership on creation and returns 404 for foreign objects.

```diff
- SELECT id,owner,title,body FROM notes WHERE id = ?
+ SELECT * FROM notes WHERE id=? AND owner_id=?
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:320.

Proof: test_f02_owner_isolation_and_mass_assignment. See evidence/audit/regression.xml and frontend/src/App.test.tsx. These retained tests verify the rejected attack and relevant legitimate behavior. Every baseline behavior also retains its exact machine-generated request/response evidence in evidence/audit/baseline.json.

### Fix for F-03

Registration always inserts role=user; admin-only routes check the role loaded from the database. No public role-change route exists.

```diff
- role = request.form.get("role") or ... or "user"
+ INSERT INTO users (username,password_hash,role,created_at) VALUES (?,?,'user',?)
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:232.

Proof: test_f03_registration_never_accepts_admin_role. See evidence/audit/regression.xml and frontend/src/App.test.tsx. These retained tests verify the rejected attack and relevant legitimate behavior. Every baseline behavior also retains its exact machine-generated request/response evidence in evidence/audit/baseline.json.

### Fix for F-04

Serve notes as JSON and render them through React text nodes. No dynamic templates, dangerous HTML rendering, eval, or HTML export; strict CSP limits browser execution.

```diff
- render_template_string("<ul>" + user_controlled_html + "</ul>")
+ <h2>{note.title}</h2><p>{note.body}</p>
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:177 and frontend/src/main.tsx.

Proof: test_f04_html_and_template_payloads_remain_data; frontend App.test.tsx. See evidence/audit/regression.xml and frontend/src/App.test.tsx. These retained tests verify the rejected attack and relevant legitimate behavior. Every baseline behavior also retains its exact machine-generated request/response evidence in evidence/audit/baseline.json.

### Fix for F-05

Remove subprocess execution entirely. An allowlist selects real JSON, CSV or text serialization of the authenticated owner’s notes; invalid formats return 400.

```diff
- subprocess.run("echo exporting notes as " + fmt, shell=True)
+ if fmt not in ('json', 'csv', 'txt'): return fail(...)
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:345.

Proof: test_f05_export_rejects_command_input. See evidence/audit/regression.xml and frontend/src/App.test.tsx. These retained tests verify the rejected attack and relevant legitimate behavior. Every baseline behavior also retains its exact machine-generated request/response evidence in evidence/audit/baseline.json.

### Fix for F-06

Use Werkzeug scrypt with per-password salts; return only allowlisted account metadata. Normal registrations require 12-128 characters; sample credentials require explicit demo mode.

```diff
- hashlib.md5(password.encode()).hexdigest()
+ generate_password_hash(password)
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:233.

Proof: test_f06_password_hashes_and_admin_redaction. See evidence/audit/regression.xml and frontend/src/App.test.tsx. These retained tests verify the rejected attack and relevant legitimate behavior. Every baseline behavior also retains its exact machine-generated request/response evidence in evidence/audit/baseline.json.

### Fix for F-07

Replace JWTs with random 256-bit opaque tokens. Store only SHA-256 token digests server-side, expire after eight hours, rotate on login and delete on logout. Use HttpOnly/SameSite cookies and Secure for HTTPS.

```diff
- jwt.decode(tok, SECRET, algorithms=["HS256", "none"])
+ SELECT * FROM sessions WHERE token_hash=? AND expires_at>?
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:160.

Proof: test_f07_session_revocation_expiry_and_forgery. See evidence/audit/regression.xml and frontend/src/App.test.tsx. These retained tests verify the rejected attack and relevant legitimate behavior. Every baseline behavior also retains its exact machine-generated request/response evidence in evidence/audit/baseline.json.

### Fix for F-08

Require a custom request header and JSON, validate Origin when supplied, and require a session-bound CSRF token on authenticated writes. Logout is POST. No cross-origin access is granted.

```diff
- @app.route("/logout")
+ if origin and origin != request.host_url.rstrip("/"): return fail(..., 403)
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:170.

Proof: test_f08_csrf_origin_and_cookie_flags. See evidence/audit/regression.xml and frontend/src/App.test.tsx. These retained tests verify the rejected attack and relevant legitimate behavior. Every baseline behavior also retains its exact machine-generated request/response evidence in evidence/audit/baseline.json.

## 6. Supply-Chain Hardening (15 pts)

Python dependencies and transitive dependencies are pinned with hashes in requirements.txt; the frontend uses package-lock.json and npm ci. The runtime is a minimal multi-stage image with pinned base-image digests, a non-root user, a read-only filesystem, dropped capabilities, no-new-privileges, resource limits and a separate data volume. Original vulnerable code, tests, local credentials and signing keys are excluded from the runtime image.

CycloneDX inventories generated by the recorded team-owned CI job: evidence/audit/ci/sbom-python.json contains 8 components; evidence/audit/ci/sbom-frontend.json contains 146 locked frontend and build components. This inventory includes development and platform-optional dependencies because the release contains the build source and lockfile. It includes React, React DOM, scheduler and Lucide, verified by the generation script; CI scans the full dependency set. The inventories describe application dependencies, not a claim of a full operating-system inventory.

Artifact: release/team-outsiders-notevault.tar.gz. This is the hardened application/build source plus compiled browser bundle and application SBOMs. It is an existing locally signed artifact from source 180958bb65578e97d60afa1b3c0cc4a723d8d581, SHA-256 587f0578afb24a4c663c7cb2192312964696d193914de6a07a66f1bc912ecadb. Its recorded runtime/build input hashes were compared with this workspace. The signature is re-verified in this audit; this is not a newly implemented release or a published container-registry signature. release/SHA256SUMS and release/provenance.json record the artifact digest and input hashes. Private key material stays in ignored .keys/ and must never be shared. The verification bundle and public key are in release/.

Independent local re-verification of the existing signed artifact:

```text
WARNING: Skipping tlog verification is an insecure practice that lacks transparency and auditability verification for the blob.
Verified OK
```

The local workflow intentionally uses a self-managed key without publishing to a transparency log; signature verification checks bytes against that public key, not the identity of the students. Keyless, transparency-backed signing is configured for a future tagged GitHub Actions run. No formal SLSA level is claimed: a locally generated manifest and signature do not independently attest to an isolated builder or reviewed source. The team must explain key custody and trusted verification inputs.

The current digest-pinned Alpine runtime passed the recorded team-owned container scan. An inherited Debian-image rejection is excluded from this report because this audit did not reproduce that earlier image comparison.

### Emerging runtime advisory review (November 2026)

The final review explicitly checked the two widely discussed “shell” advisory families instead of treating a green dependency scan as permanent evidence. Node2Shell (CVE-2026-111497) affects vulnerable Node.js Brotli decoding releases. This project pins the frontend build stage and both hosted Node setup steps to Node 24.22.1, a fixed release, and the package manifest rejects older Node 24 versions. Node is used only to compile the React bundle; the final Python/Alpine runtime contains no Node executable or Node package tree. The result is therefore **patched in the build boundary and absent from the audited container runtime**, not merely “not observed by a scanner.”

The issues informally called PHP2Shell (CVE-2026-109618 and CVE-2026-109619) affect PHP web-request runtimes. This repository has no PHP source, PHP interpreter, Composer manifest, PHP container layer, or PHP request handler. They are **not applicable to this target**. This applicability decision is evidence-scoped and is not counted as an additional NoteVault vulnerability finding. If PHP is introduced later, the deployment must use a PHP security release at or above 8.2.35, 8.3.36, 8.4.27, or 8.5.12 as appropriate and rerun the full gate.

Container runtime verification: passed; non-root UID 10001:10001, read-only root, loopback-only port and expected marker verified in evidence/audit/ci/container-check.json.

Container vulnerability scan: 0 HIGH/CRITICAL issues in the scanned image (see evidence/audit/ci/sca-container.json).

## 7. Security CI Pipeline (10 pts)

.github/workflows/security.yml installs hash-locked dependencies, runs backend and frontend regression tests, builds the client, runs Bandit SAST, pip-audit SCA, npm audit, Gitleaks secret scanning, a container scan and a real container health/configuration check. It produces SBOMs and release artifacts. Full commit hashes pin third-party Actions. Pull-request jobs have read-only repository access; only tagged release signing receives the OIDC permission it requires.

The SAST gate fails on HIGH findings at MEDIUM/HIGH confidence; pip-audit fails on any known Python vulnerability, npm audit fails at HIGH, the container gate fails on HIGH/CRITICAL, and Gitleaks fails on detected secrets. Tool failures are not treated as success. Historical intentionally vulnerable lab source is excluded from the hardened release scan and kept only for the assessment; generated packages, local state and evidence are also excluded from secret scans using the committed configuration.

Recorded team-owned CI scan evidence is in evidence/audit/ci/sast.json; evidence/audit/ci/sca-python.json; evidence/audit/ci/sca-npm.json. scripts/prove_gate.py creates a temporary nonexecuted shell-injection fixture and confirms that the same Bandit threshold returns nonzero. The CI fixture rejection is in evidence/audit/ci/gate-rejection.json. Hosted GitHub Actions status: Passed security job at https://github.com/6631503097/notevault-team-outsiders/actions/runs/42068311164 on 82d6f4a05bb2bf3c92fd5d5b19ba56bb8c5fec2f; tag-only signing skipped. The intentional local failing-gate proof remains the negative control.

## 8. Conclusion & Reflection (5 pts - clarity)

The verified baseline failures are addressed by removing unsafe interpretation, enforcing authorization at data access, using modern password hashing and revocable sessions, and making builds auditable. Tests also check legitimate note lifecycles, persistence, cross-database token rejection, CSV export protection, rate limiting and concurrent edits.

Residual risks: this is a single-instance course app with visible demo credentials only when local demo mode is explicitly enabled; it has no MFA/recovery, centralized alerts, immutable logs or encrypted notes at rest. SQLite and local key custody trust the machine operator. Each account is limited to 1,000 notes including removed notes; the admin directory is bounded to 500 accounts. External deployment ownership, reverse-proxy configuration, remote persistence and remote service isolation are not established by the local tests. Backup/restore and monitoring work remain.

AI-assisted technical assessment, not a student personal reflection: the strongest improvement was not any single patch, but the traceable chain from a harmless exploit to its root cause, focused remediation, regression proof, dependency and container gates, SBOM, and signed release. This audit checked the current locked dependencies and recorded actual scan results. An inherited story about detecting and upgrading Werkzeug, Vitest and Alpine issues is excluded because those upgrades were not performed in this audit. The next hardening priorities are MFA/recovery, encrypted backups, centralized monitoring, immutable audit storage, and a hosted keyless release signature.

## Appendix

### Current team handoff status

The presentation URL was supplied by Wanna San on 6 November 2026. Anonymous HTTP retrieval returned the Drive viewer for the MP4; this is not a playback/audio check. Latest verified remediation CI passed on 040b78e46865e30f58149b8e0286c7355eadb268: https://github.com/6631503097/notevault-team-outsiders/actions/runs/42170648164 . Follow-up evidence branch CI passed on 76ccb728ac3291016d1b0a9b875b23752e003f39: https://github.com/6631503097/notevault-team-outsiders/actions/runs/42190990151 . These observations supplement the earlier audited scan artifacts; they do not claim CI on later report-only edits. The recording itself has not been watched by the assistant. At the last verified GitHub check, Myo review PRs 1 and 3 and Zaw PR 2 were merged. Wanna guided-review PR 4 was merged; follow-up evidence PR 5 was still draft. No submitted GitHub reviews were recorded on these PRs. Wanna subsequently reported that all members completed their personal work. Zaw confirmation/signature fields remain unfinished in the last fetched remediation worksheet. Wanna explicitly confirmed her personal F-01/F-05 statement in chat on 6 November 2026; that confirmation is transcribed in the review branch worksheet and below, with assistant commit authorship preserved. This report does not attest those personal actions or claim portal submission.

### Wanna San - confirmed personal reflection

Wanna San (6631503097) explicitly confirmed the following statement in chat on 6 November 2026; the assistant transcribed it rather than signing on her behalf:

"I, Wanna San, reviewed and understand the F-01/F-05 code and results and personally ran the saved capture commands. I learned that parameterized SQL and ownership checks solve separate problems, and that removing shell execution eliminates the demonstrated export command injection. I confirm this describes my own work. - Wanna San, 6 November 2026"

The saved records contain six passing focused tests. The screenshots display retained results and were captured by the assistant. This confirmation does not attribute inherited implementation or assistant commits to Wanna.

### Final submission controls

| Control | Status | Evidence or required action |
|---|---|---|
| Threat model, findings, fixes | Complete | Sections 3-5; linked evidence and commit references |
| Tests, SAST, SCA, secrets, container | Check evidence scope and hosted commit | Verification-at-a-glance table; evidence/audit/provenance.json |
| SBOM, signed artifact, provenance | Local integrity evidence; not student identity | Section 6 and release directory |
| Team repository and local app | Verified within stated scope | External deployment ownership is unverified; nutthakorn7 write invitation sent, acceptance pending |
| All three members review and understand work | Required before upload | Student attestation; not inferable from repository state |
| Recorded demo URL | Supplied by team | Linked on cover; signed-out playback must be confirmed by team |
| Private peer ratings | Required separately | Each member submits truthful rating and one-line reason |
| Portal upload with term-project code | Required | One representative uploads this PDF after all controls above are satisfied |

The report is due Friday, November 6 at 16:59 Bangkok time. One representative uploads the final PDF at https://learn.zcr.ai/submit with the private project code from Classroom. Use the project code, not a weekly worksheet code. The team repository and local app are present; the presentation link is supplied; portal upload and private peer ratings are not verified.

### Tools and evidence index

Flask test client and pytest reproduce and verify API behavior. React Testing Library/Vitest check rendering, saving and draft protection. Bandit, pip-audit, npm audit and Gitleaks generate scan reports. Docker builds the runtime; Trivy scans its packages; CycloneDX inventories dependencies; Cosign signs and verifies a local release. Full commands and scripts live in scripts/; original source is in lab/original/. The team marker is 3d821afbe8a0 and the baseline source digest is 2d25d7dc1282cf743c9702e910f090b81fad6272a8b8793156d8431c5ab3aaa6.

### Task split and authorship

Membership is recorded on the cover. The implementation, initial tests, harness and original report design were inherited with an AI/shared-source disclosure. Independent verification and CI corrections in this conversation are separate work. Student-submitted evidence and reflections retain their own authorship and are not presented as assistant-generated evidence. Actual student review, reproduction, demo work, and peer ratings must be recorded truthfully by Zaw Win Htut, Wanna San, and Myo Zin Thant; the repository cannot establish those personal actions on their behalf.

### Provenance and evidence limits

The implementation, initial findings, tests and report generator arrived in the supplied bundle. The assistant did not create them anew in this conversation. The original shared-AI disclosure is retained. Independently executed checks are recorded with commands, timestamps, exit codes and output hashes in evidence/audit/execution-journal.json. CI evidence is accepted only for files rewritten by the observed workflow steps, not every file that happened to be uploaded with an artifact.

Inherited staging CI records, the earlier rejected-image scan, and the unverified external-deployment narrative are excluded as proof of this assessment. Equal hashes do not by themselves establish origin: a successful empty scan or reproducible SBOM can legitimately match an earlier file byte-for-byte. The first local frontend attempt timed out while starting its worker and executed no tests. The unchanged source, copied and hash-compared in a temporary directory, then passed three tests and the production build. Both attempts are retained; the failed attempt is not counted as a pass. No finding is treated as verified solely because its team marker matches. See docs/EVIDENCE-PROVENANCE-AUDIT.md for the claim-by-claim disposition.

### References

- Assignment requirements: the user-supplied software_security_project_prompt_guide.md. No claim is made that this audit accessed a private Classroom announcement.
- Course source snapshot: project/starter-app/app.py at verified revision 6996818be46cfb3f26b9b9d88e7c95af7ae32176; evidence/audit/course-source-check.json.
- Original report headings: docs/COURSE-REPORT-TEMPLATE.md.
- OWASP Top 10:2025: https://owasp.org/Top10/2025/
- OWASP API1:2023: https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/
- CWE definitions: https://cwe.mitre.org/data/definitions/89.html (substitute each listed CWE number).
- Flask security guidance: https://flask.palletsprojects.com/en/stable/web-security/
- React rendering: https://react.dev/learn
- Cosign signing and verification: https://docs.sigstore.dev/cosign/signing/signing_with_blobs/
- Node.js October 2026 security releases (CVE-2026-111497): https://nodejs.org/en/blog/vulnerability/october-2026-security-releases
- PHP critical RCE security advisory (CVE-2026-109618 and CVE-2026-109619): https://www.php.net/archive/2026.php#2026-10-21-5
