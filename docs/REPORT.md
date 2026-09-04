# Term Project Report - Secure Build

## Cover

| Field | Value |
|---|---|
| Team name | Team Outsiders |
| Members (name + ID) | Zaw Win Htut 6631503101; Wanna San 6631503097; Myo Zin Thant 6631503076 |
| Target application | Provided NoteVault, upgraded to Fieldnotes |
| Repository URL | https://github.com/Thiha-Lynn/notevault-team-outsiders (private; instructor access must be granted) |
| Live application | https://outsiders.3-0-126-159.nip.io/ |
| Date | 2026-09-04 |
| Team marker | 3d821afbe8a0 |
| Status | Evidence-backed implementation draft; team review and submission work remain |

## AI-tool usage disclosure

OpenAI Codex assisted with requirements review, implementation, tests, local vulnerability reproduction, build/security tooling and this report. Both teams received shared AI-assisted code in the same session. Different team names and markers do not make shared source independently authored. See docs/AI-DISCLOSURE.md. Students must disclose this assistance, independently reproduce and understand results, and confirm acceptance of the shared scaffolding with the instructor. No student authorship, weekly history, hosted CI run or personal reflection is fabricated.

## 1. Executive Summary

Team Outsiders uses NoteVault as a local private notebook with account registration, sessions, owner-scoped notes and exports. Its Fieldnotes interface organizes notes into Fieldwork, Research, Personal. The assessment verified ten harmless baseline probes grouped into eight findings: two Critical, four High, and two Medium, using qualitative severity. The critical risks are shell injection and session forgery; authorization, SQL construction, interpreted content and password handling add further risk.

The new React/TypeScript client and Flask API remove the demonstrated mechanisms, retain legitimate application behavior and add persistent storage, conflict detection and reversible note removal. The security regression suite and frontend tests exercise both successful use and rejected attacks. Original source and actual probe outputs are retained. This draft does not claim a grade, independent team authorship, identity-stamped screenshots, a hosted Actions run, or a completed live/video demo.

## 2. System Scope & Function

The application provides local account creation/sign-in, note creation/view/edit, literal search, collections, pin/archive/restore, CSV/JSON/text downloads, personal audit history, a protected team directory, and an administrator account listing without passwords. Notes remain private per user, even for administrators. Both teams use separate projects, databases, volumes, cookies and ports.

The original assessment target is lab/original/app.py from course revision 6996818be46cfb3f26b9b9d88e7c95af7ae32176. It is excluded from runtime/release packaging. scripts/reproduce_baseline.py loads it in a separate old-dependency environment and temporary SQLite database; it does not start a listener.

Data-flow diagram: docs/dfd.svg and docs/THREAT-MODEL.md. Trust boundaries separate the browser, Flask process, local database and build/release pipeline. The live deployment terminates HTTPS in Nginx and forwards only to loopback Gunicorn. Protected assets include private notes, password hashes, session tokens, audit records and release integrity. Real university services and real credentials are out of scope.

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

Run the steps in docs/BASELINE.md. Every probe is linked to the exact team marker and original-source digest in evidence/baseline.json. Only temporary fake data is used.

### Finding F-01 - SQL injection in login and search

| Field | Value |
|---|---|
| CWE | CWE-89 |
| OWASP 2025 | A05:2025 Injection |
| Severity | High |
| Location | lab/original/app.py:128; login / search |
| Evidence | evidence/baseline.json, finding F-01, team marker 3d821afbe8a0 |

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
| Evidence | evidence/baseline.json, finding F-02, team marker 3d821afbe8a0 |

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
| Evidence | evidence/baseline.json, finding F-03, team marker 3d821afbe8a0 |

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
| Evidence | evidence/baseline.json, finding F-04, team marker 3d821afbe8a0 |

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
| Evidence | evidence/baseline.json, finding F-05, team marker 3d821afbe8a0 |

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
| Evidence | evidence/baseline.json, finding F-06, team marker 3d821afbe8a0 |

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
| Evidence | evidence/baseline.json, finding F-07, team marker 3d821afbe8a0 |

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
| Evidence | evidence/baseline.json, finding F-08, team marker 3d821afbe8a0 |

Reproduction: Send an authenticated form POST to /notes with Origin: https://attacker.invalid and no CSRF token. The old server accepts it. Browser exploitability depends on its cookie defaults and is not universally asserted.

Impact: The server does not distinguish legitimate state changes from attacker-origin requests carrying credentials; logout also mutates state on GET.

Root cause: No CSRF token or origin validation is required. Cookie attributes are weak.

## 5. Remediation (25 pts)

The original source is preserved rather than rewritten. The application upgrade requested by the user is broader than a minimal patch; each security change below is tied to the specific unsafe mechanism. All listed fixes are in the actual AI-assisted remediation commit, not attributed to a student.

### Fix for F-01

Use bound SQL parameters, fetch the canonical user row, and verify its password hash. Search binds both owner ID and escaped literal search text.

```diff
- q = "SELECT * FROM users WHERE username = ..." % username
+ row = db().execute("SELECT * FROM users WHERE username=?", (name,)).fetchone()
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:253.

Proof: test_f01_sql_injection_login_and_search. See evidence/regression.xml and frontend/src/App.test.tsx. These tests verify the rejected attack and relevant legitimate behavior. Grading screenshots still need to be captured by the team with the required real identity/date stamp.

### Fix for F-02

Every read and write constrains both the note ID and authenticated owner ID. The server supplies ownership on creation and returns 404 for foreign objects.

```diff
- SELECT id,owner,title,body FROM notes WHERE id = ?
+ SELECT * FROM notes WHERE id=? AND owner_id=?
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:320.

Proof: test_f02_owner_isolation_and_mass_assignment. See evidence/regression.xml and frontend/src/App.test.tsx. These tests verify the rejected attack and relevant legitimate behavior. Grading screenshots still need to be captured by the team with the required real identity/date stamp.

### Fix for F-03

Registration always inserts role=user; admin-only routes check the role loaded from the database. No public role-change route exists.

```diff
- role = request.form.get("role") or ... or "user"
+ INSERT INTO users (username,password_hash,role,created_at) VALUES (?,?,'user',?)
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:232.

Proof: test_f03_registration_never_accepts_admin_role. See evidence/regression.xml and frontend/src/App.test.tsx. These tests verify the rejected attack and relevant legitimate behavior. Grading screenshots still need to be captured by the team with the required real identity/date stamp.

### Fix for F-04

Serve notes as JSON and render them through React text nodes. No dynamic templates, dangerous HTML rendering, eval, or HTML export; strict CSP limits browser execution.

```diff
- render_template_string("<ul>" + user_controlled_html + "</ul>")
+ <h2>{note.title}</h2><p>{note.body}</p>
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:177 and frontend/src/main.tsx.

Proof: test_f04_html_and_template_payloads_remain_data; frontend App.test.tsx. See evidence/regression.xml and frontend/src/App.test.tsx. These tests verify the rejected attack and relevant legitimate behavior. Grading screenshots still need to be captured by the team with the required real identity/date stamp.

### Fix for F-05

Remove subprocess execution entirely. An allowlist selects real JSON, CSV or text serialization of the authenticated owner’s notes; invalid formats return 400.

```diff
- subprocess.run("echo exporting notes as " + fmt, shell=True)
+ if fmt not in ('json', 'csv', 'txt'): return fail(...)
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:345.

Proof: test_f05_export_rejects_command_input. See evidence/regression.xml and frontend/src/App.test.tsx. These tests verify the rejected attack and relevant legitimate behavior. Grading screenshots still need to be captured by the team with the required real identity/date stamp.

### Fix for F-06

Use Werkzeug scrypt with per-password salts; return only allowlisted account metadata. Normal registrations require 12-128 characters; sample credentials require explicit demo mode.

```diff
- hashlib.md5(password.encode()).hexdigest()
+ generate_password_hash(password)
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:233.

Proof: test_f06_password_hashes_and_admin_redaction. See evidence/regression.xml and frontend/src/App.test.tsx. These tests verify the rejected attack and relevant legitimate behavior. Grading screenshots still need to be captured by the team with the required real identity/date stamp.

### Fix for F-07

Replace JWTs with random 256-bit opaque tokens. Store only SHA-256 token digests server-side, expire after eight hours, rotate on login and delete on logout. Use HttpOnly/SameSite cookies and Secure for HTTPS.

```diff
- jwt.decode(tok, SECRET, algorithms=["HS256", "none"])
+ SELECT * FROM sessions WHERE token_hash=? AND expires_at>?
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:160.

Proof: test_f07_session_revocation_expiry_and_forgery. See evidence/regression.xml and frontend/src/App.test.tsx. These tests verify the rejected attack and relevant legitimate behavior. Grading screenshots still need to be captured by the team with the required real identity/date stamp.

### Fix for F-08

Require a custom request header and JSON, validate Origin when supplied, and require a session-bound CSRF token on authenticated writes. Logout is POST. No cross-origin access is granted.

```diff
- @app.route("/logout")
+ if origin and origin != request.host_url.rstrip("/"): return fail(..., 403)
```

Commit: a19ccf2926cc72c22ebe3f7084bae943c973d8bf. Location: backend/app.py:170.

Proof: test_f08_csrf_origin_and_cookie_flags. See evidence/regression.xml and frontend/src/App.test.tsx. These tests verify the rejected attack and relevant legitimate behavior. Grading screenshots still need to be captured by the team with the required real identity/date stamp.

## 6. Supply-Chain Hardening (15 pts)

Python dependencies and transitive dependencies are pinned with hashes in requirements.txt; the frontend uses package-lock.json and npm ci. The runtime is a minimal multi-stage image with pinned base-image digests, a non-root user, a read-only filesystem, dropped capabilities, no-new-privileges, resource limits and a separate data volume. Original vulnerable code, tests, local credentials and signing keys are excluded from the runtime image.

CycloneDX inventories: evidence/sbom-python.json contains 8 components; evidence/sbom-frontend.json contains 146 locked frontend and build components. This inventory includes development and platform-optional dependencies because the release contains the build source and lockfile. It includes React, React DOM, scheduler and Lucide, verified by the generation script; CI scans the full dependency set. The inventories describe application dependencies, not a claim of a full operating-system inventory.

Artifact: release/team-outsiders-notevault.tar.gz. This is the hardened application/build source plus compiled browser bundle and application SBOMs. It is signed locally with Cosign; it is not a published container registry signature. release/SHA256SUMS and release/provenance.json record the artifact digest and input hashes. Private key material stays in ignored .keys/ and must never be shared. The verification bundle and public key are in release/.

Actual local verification output:

```text
Local key signature; transparency log intentionally not used.
WARNING: Skipping tlog verification is an insecure practice that lacks transparency and auditability verification for the blob.
Verified OK
```

The local workflow intentionally uses a self-managed key without publishing to a transparency log; signature verification checks bytes against that public key, not the identity of the students. Keyless, transparency-backed signing is configured for a future tagged GitHub Actions run. No formal SLSA level is claimed: a locally generated manifest and signature do not independently attest to an isolated builder or reviewed source. The team must explain key custody and trusted verification inputs.

The initial Debian runtime image was rejected by the HIGH/CRITICAL gate. The current runtime uses a digest-pinned Alpine base; the original rejection is retained in evidence/container-base-rejected.json.

Container runtime verification: passed; non-root UID 10001:10001, read-only root, loopback-only port and expected marker verified in evidence/container-check.json.

Container vulnerability scan: 0 HIGH/CRITICAL issues in the scanned image (see evidence/sca-container.json).

## 7. Security CI Pipeline (10 pts)

.github/workflows/security.yml installs hash-locked dependencies, runs backend and frontend regression tests, builds the client, runs Bandit SAST, pip-audit SCA, npm audit, Gitleaks secret scanning, a container scan and a real container health/configuration check. It produces SBOMs and release artifacts. Full commit hashes pin third-party Actions. Pull-request jobs have read-only repository access; only tagged release signing receives the OIDC permission it requires.

The SAST gate fails on HIGH findings at MEDIUM/HIGH confidence; pip-audit fails on any known Python vulnerability, npm audit fails at HIGH, the container gate fails on HIGH/CRITICAL, and Gitleaks fails on detected secrets. Tool failures are not treated as success. Historical intentionally vulnerable lab source is excluded from the hardened release scan and kept only for the assessment; generated packages, local state and evidence are also excluded from secret scans using the committed configuration.

Local pass evidence is in evidence/security-gate.json. scripts/prove_gate.py creates a temporary nonexecuted shell-injection fixture and confirms that the same Bandit threshold returns nonzero. The actual rejection is in evidence/gate-rejection.json. Hosted GitHub Actions status: Not run - repository URL not provided. The intentional local failing-gate proof remains the negative control.

## 8. Conclusion & Reflection (5 pts - clarity)

The verified baseline failures are addressed by removing unsafe interpretation, enforcing authorization at data access, using modern password hashing and revocable sessions, and making builds auditable. Tests also check legitimate note lifecycles, persistence, cross-database token rejection, CSV export protection, rate limiting and concurrent edits.

Residual risks: this is a single-instance course app with visible demo credentials only when local demo mode is explicitly enabled; it has no MFA/recovery, centralized alerts, immutable logs or encrypted notes at rest. SQLite and local key custody trust the machine operator. Each account is limited to 1,000 notes including removed notes; the admin directory is bounded to 500 accounts. The live deployment uses HTTPS, an exact trusted host, fresh non-demo data and separate service identities; backup/restore and monitoring work remain.

Student reflection is pending. Each team member should write what they personally reproduced, what failed, why their fix is appropriate and which residual risk they would address next. Do not present this implementation session as semester-long individual contribution.

## Appendix

### Milestones and remaining submission work

| Milestone | Due | Status |
|---|---|---|
| Team + target | Week 4 | Names supplied; NoteVault retained; House and registration confirmation remain |
| Threat model | Week 7 | DFD, STRIDE and ranked-risk draft included; team review pending |
| Vulnerability report | Week 11 | Actual local probe and regression evidence included; student screenshots pending |
| Remediation + SBOM + signature | Week 14 | Code, local SBOMs and local signature present; team review required |
| WIP demo + peer review | Week 16 | Runbook provided; actual demo and feedback pending |
| Final report + prerecorded demo + Q&A | Week 19 | Repository and live URLs added; final PDF review, video and live Q&A remain |

Actual calendar deadlines and the project submission code were not supplied. Use the project code, not a weekly worksheet code. Repository and live deployment are present; portal upload, peer rating and video submission remain.

### Tools and evidence index

Flask test client and pytest reproduce and verify API behavior. React Testing Library/Vitest check rendering, saving and draft protection. Bandit, pip-audit, npm audit and Gitleaks generate scan reports. Docker builds the runtime; Trivy scans its packages; CycloneDX inventories dependencies; Cosign signs and verifies a local release. Full commands and scripts live in scripts/; original source is in lab/original/. The team marker is 3d821afbe8a0 and the baseline source digest is 2d25d7dc1282cf743c9702e910f090b81fad6272a8b8793156d8431c5ab3aaa6.

### Task split and authorship

Membership is recorded on the cover. Actual student tasks and reviewers must be recorded in docs/WEEKLY-LOG.md. No member has been assigned credit for this AI-assisted implementation. Each member should reproduce different findings, review the other members’ work, and be able to explain the full system. The course's peer-rating procedure remains private student work.

### References

- Google Classroom project announcement, August 16: https://classroom.google.com/c/ODU1NTkwNjAzNzg2 (read on 2026-09-04).
- Course project brief: repo/project/README.md, revision 6996818be46cfb3f26b9b9d88e7c95af7ae32176.
- Original report headings: docs/COURSE-REPORT-TEMPLATE.md.
- OWASP Top 10:2025: https://owasp.org/Top10/2025/
- OWASP API1:2023: https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/
- CWE definitions: https://cwe.mitre.org/data/definitions/89.html (substitute each listed CWE number).
- Flask security guidance: https://flask.palletsprojects.com/en/stable/web-security/
- React rendering: https://react.dev/learn
- Cosign signing and verification: https://docs.sigstore.dev/cosign/signing/signing_with_blobs/
