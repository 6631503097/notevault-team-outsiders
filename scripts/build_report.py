"""Build an evidence-linked Markdown and PDF draft without inventing student work."""
from datetime import datetime,timezone
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
team=json.loads((ROOT/'team.json').read_text())
E=ROOT/'evidence'
base=json.loads((E/'baseline.json').read_text())
fix=subprocess.check_output(['git','log','--format=%H','--grep=fix(F-01','-1'],cwd=ROOT,text=True).strip()
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()

def line(path,needle):
    return next(i for i,l in enumerate((ROOT/path).read_text().splitlines(),1) if needle in l)

def count_components(name):
    p=E/name
    return len(json.loads(p.read_text()).get('components',[])) if p.exists() else 0

findings=[
('F-01','SQL injection in login and search','High','CWE-89','A05:2025 Injection','login / search',
 "Log in with username admin\' -- and an incorrect password; the old route returns a session cookie. Separately, authenticate as Alice and search for \' OR 1=1 -- . The response includes the administrator’s team marker.",
 'The attacker bypasses the credential check and can read notes across owner boundaries using the search query. The bypassed login’s subject is the supplied string; the evidence does not falsely claim that this SQLi alone yields a normal administrator subject.',
 'SQL strings interpolate username and search terms.','Use bound SQL parameters, fetch the canonical user row, and verify its password hash. Search binds both owner ID and escaped literal search text.',
 'q = "SELECT * FROM users WHERE username = ..." % username','row = db().execute("SELECT * FROM users WHERE username=?", (name,)).fetchone()',
 'test_f01_sql_injection_login_and_search','q = "SELECT * FROM users','row = db().execute("SELECT * FROM users WHERE username=?"'),
('F-02','Broken object-level authorization','High','CWE-639','A01:2025 Broken Access Control / API1:2023 BOLA','GET /api/notes/3',
 'Authenticate as Alice in the original app and request /api/notes/3. The JSON owner is admin, and the body contains this team’s marker.',
 'Any signed-in user can enumerate private notes belonging to other accounts.',
 'The original lookup checks only the object ID.','Every read and write constrains both the note ID and authenticated owner ID. The server supplies ownership on creation and returns 404 for foreign objects.',
 'SELECT id,owner,title,body FROM notes WHERE id = ?','SELECT * FROM notes WHERE id=? AND owner_id=?',
 'test_f02_owner_isolation_and_mass_assignment','SELECT id,owner,title,body FROM notes WHERE id','SELECT * FROM notes WHERE id=? AND owner_id=?'),
('F-03','Role escalation during registration','High','CWE-269 / CWE-915','A01:2025 Broken Access Control','POST /register',
 'Register probe_user with role=admin, log in, then request /admin. The original app grants administrator access.',
 'An untrusted registrant receives a privileged role and can list accounts and password digests.',
 'Registration trusts the client-supplied role.','Registration always inserts role=user; admin-only routes check the role loaded from the database. No public role-change route exists.',
 'role = request.form.get("role") or ... or "user"',"INSERT INTO users (username,password_hash,role,created_at) VALUES (?,?,'user',?)",
 'test_f03_registration_never_accepts_admin_role','role = request.form.get','VALUES (?,?,\'user\',?)'),
('F-04','Stored HTML injection and server template evaluation','High','CWE-79 / CWE-1336','A05:2025 Injection','POST /notes; GET /; GET /search',
 'Save <img src=x onerror=alert(1)> and retrieve the home page: the HTML appears unescaped. Save {{7*7}} and search for 7*7: the original response renders Template probe: 49.',
 'Stored content is interpreted as HTML or a template. The harmless expression proves server-side template evaluation. A browser alert or arbitrary-code-execution screenshot is not claimed.',
 'The original home marks concatenated HTML safe; search concatenates untrusted data into template source.','Serve notes as JSON and render them through React text nodes. No dynamic templates, dangerous HTML rendering, eval, or HTML export; strict CSP limits browser execution.',
 'render_template_string("<ul>" + user_controlled_html + "</ul>")','<h2>{note.title}</h2><p>{note.body}</p>',
 'test_f04_html_and_template_payloads_remain_data; frontend App.test.tsx','return render_template_string("<a href=/','resp.headers["Content-Security-Policy"]'),
('F-05','Shell command injection in export','Critical','CWE-78','A05:2025 Injection','GET /export?fmt=...',
 'As Alice, request fmt=txt; printf NV_SAFE_PROBE. The original response contains NV_SAFE_PROBE, proving that the additional harmless shell command ran.',
 'An authenticated attacker controls a shell command executed as the application user. Only a harmless output marker was executed during verification.',
 'The export route concatenates fmt into a command passed with shell=True.','Remove subprocess execution entirely. An allowlist selects real JSON, CSV or text serialization of the authenticated owner’s notes; invalid formats return 400.',
 'subprocess.run("echo exporting notes as " + fmt, shell=True)',"if fmt not in ('json', 'csv', 'txt'): return fail(...)",
 'test_f05_export_rejects_command_input','out = subprocess.run','if fmt not in ("json", "csv", "txt")'),
('F-06','Fast password digests and digest disclosure','Medium','CWE-916 / CWE-200','A04:2025 Cryptographic Failures','users table; GET /admin',
 'After reproducing role escalation, request /admin and compare the exposed administrator digest to the MD5 of the known sample password. Both are identical.',
 'An account-table leak gives attackers unsalted fast password digests suitable for offline guessing. Severity rises when chained with F-03. No real account credential was tested.',
 'MD5 is used as an unsalted password digest, and the admin response includes that digest.','Use Werkzeug scrypt with per-password salts; return only allowlisted account metadata. Normal registrations require 12-128 characters; sample credentials require explicit demo mode.',
 'hashlib.md5(password.encode()).hexdigest()','generate_password_hash(password)',
 'test_f06_password_hashes_and_admin_redaction','hashlib.md5(password.encode())','name, generate_password_hash(password), int(time.time())'),
('F-07','Forgeable sessions signed with a source-code secret','Critical','CWE-321 / CWE-613','A07:2025 Authentication Failures','session cookie; GET /admin',
 'Use the known constant SECRET in the original source to sign an HS256 token with sub=admin, then request /admin with that cookie. The response is 200.',
 'Anyone with the source secret can impersonate the administrator. This does not rely on or claim an alg=none bypass.',
 'A hard-coded JWT key is shared with all deployments, and tokens lack enforced expiry and server revocation.','Replace JWTs with random 256-bit opaque tokens. Store only SHA-256 token digests server-side, expire after eight hours, rotate on login and delete on logout. Use HttpOnly/SameSite cookies and Secure for HTTPS.',
 'jwt.decode(tok, SECRET, algorithms=["HS256", "none"])','SELECT * FROM sessions WHERE token_hash=? AND expires_at>?',
 'test_f07_session_revocation_expiry_and_forgery','SECRET =','SELECT * FROM sessions WHERE token_hash=? AND expires_at>?'),
('F-08','Missing request protection for state changes','Medium','CWE-352','A01:2025 Broken Access Control','POST /notes; GET /logout',
 'Send an authenticated form POST to /notes with Origin: https://attacker.invalid and no CSRF token. The old server accepts it. Browser exploitability depends on its cookie defaults and is not universally asserted.',
 'The server does not distinguish legitimate state changes from attacker-origin requests carrying credentials; logout also mutates state on GET.',
 'No CSRF token or origin validation is required. Cookie attributes are weak.','Require a custom request header and JSON, validate Origin when supplied, and require a session-bound CSRF token on authenticated writes. Logout is POST. No cross-origin access is granted.',
 '@app.route("/logout")','if origin and origin != request.host_url.rstrip("/"): return fail(..., 403)',
 'test_f08_csrf_origin_and_cookie_flags','@app.route("/logout")','if origin and origin != request.host_url.rstrip("/")')
]

stride='''| Element or flow | STRIDE risks | Mitigation and residual risk |
|---|---|---|
| Browser to API | Spoofing, tampering, information disclosure, elevation | Opaque sessions, JSON + CSRF, owner predicates, escaping and CSP. HTTPS is required outside loopback. |
| Registration/login | Spoofing, denial of service, elevation | Server-selected role, scrypt, generic errors, persistent IP throttle. No MFA or recovery flow. |
| Notes API to SQLite | Tampering, information disclosure, elevation | Parameters, owner IDs, foreign keys, versions and input limits. A host/database operator can still read data. |
| Export to browser | Tampering, information disclosure | Owner-scoped serialization, format allowlist, attachment download and CSV formula protection. Downloaded files become the user’s responsibility. |
| Audit history | Repudiation, tampering | Record actor, action, object and timestamp. Local logs are not immutable or externally monitored. |
| Dependencies/build/release | Tampering, elevation, information disclosure | Lockfiles with hashes, pinned base images/actions, scan gates, SBOM and signatures. Trust still includes registries, build tools and signing-key custody. |'''
risks='''| Rank | Threat | Likelihood x impact (1-5) | Before / mitigation |
|---|---|---|---|
| 1 | F-05 shell execution | 5 x 5 = 25 | Arbitrary commands; remove the shell completely. |
| 2 | F-07 session forgery | 5 x 5 = 25 | Impersonation; random, expiring, revocable server sessions. |
| 3 | F-01 injection | 5 x 4 = 20 | Query manipulation; bind all user values. |
| 4 | F-02/F-03 authorization | 5 x 4 = 20 | Cross-user data and roles; server-side authorization. |
| 5 | F-04 interpreted stored content | 4 x 5 = 20 | HTML/template injection; typed JSON and text rendering. |'''
mermaid='''flowchart LR
  subgraph Client["TB1: User-controlled browser"]
    U[User or administrator]
    R[React interface]
    U --> R
  end
  subgraph Server["TB2: App process / container"]
    A[Flask API and authorization]
    X[JSON / CSV / text serializer]
    A --> X
  end
  subgraph Store["TB3: Persistent local storage"]
    D[(SQLite: accounts, notes, sessions, audit)]
  end
  R -->|JSON + opaque cookie + CSRF| A
  A -->|Owner-scoped parameterized SQL| D
  D --> A
  X -->|Owned notes attachment| R
  subgraph Build["TB4: Supply chain and release"]
    G[Source + locked packages]
    C[Security CI]
    S[SBOM + signed artifact]
    G --> C --> S
  end
  S -.->|Verified release| A
'''
(ROOT/'docs/THREAT-MODEL.md').write_text(f'# {team["id"]} - NoteVault threat model\n\n'
    f'Team marker: `{base["marker"]}`. Application edition: {team["edition"]}.\n\n'
    'Assets: private notes, account password hashes, session tokens, team identity, audit history, source code, dependency inventory and release integrity. Attackers: unauthenticated registrants, malicious authenticated users, compromised dependencies, and a local privileged operator. Real university systems, real credentials and other teams’ databases are out of scope.\n\n'
    '## Data-flow diagram\n\n```mermaid\n'+mermaid+'```\n\n'
    f'The local preview is loopback-only. The live service at {team["live_url"]} uses HTTPS and a loopback-only application process behind Nginx. The runtime contains only the hardened application; the original vulnerable app is accessed by an isolated test client.\n\n## STRIDE\n\n'+stride+'\n\n## Top risks\n\n'+risks+'\n\nThese qualitative scores prioritize remediation; they are not calculated CVSS scores or a guarantee of residual safety.\n')

svg='''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="420" viewBox="0 0 1000 420"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#415d56"/></marker></defs><rect width="1000" height="420" fill="#ffffff"/><g font-family="Arial,sans-serif" fill="#233b35"><text x="20" y="28" font-size="20">NoteVault - data flows and trust boundaries</text><g stroke="#9aac9d" fill="#f4f7f2" stroke-dasharray="6 4"><rect x="20" y="55" width="230" height="190" rx="12"/><rect x="365" y="55" width="270" height="190" rx="12"/><rect x="750" y="55" width="230" height="190" rx="12"/><rect x="20" y="295" width="615" height="105" rx="12"/></g><g font-size="14"><text x="38" y="82">TB1 - browser</text><text x="383" y="82">TB2 - app container</text><text x="768" y="82">TB3 - storage</text><text x="38" y="322">TB4 - build and supply chain</text></g><g font-size="17" text-anchor="middle"><text x="135" y="135">User / administrator</text><text x="135" y="164">React interface</text><text x="500" y="135">Flask API</text><text x="500" y="164">Authorization / export</text><text x="865" y="132">SQLite</text><text x="865" y="161">Notes / accounts</text><text x="865" y="190">Sessions / audit</text></g><g fill="none" stroke="#415d56" stroke-width="2" marker-end="url(#arrow)"><path d="M250 120 H365"/><path d="M365 202 H250"/><path d="M635 120 H750"/><path d="M750 202 H635"/><path d="M500 295 V245"/></g><g font-size="12" text-anchor="middle"><text x="307" y="106">JSON + cookie</text><text x="307" y="145">+ CSRF</text><text x="307" y="226">Owned export</text><text x="693" y="106">Bound SQL</text><text x="693" y="226">Owned records</text><text x="564" y="275">Verified build</text></g><text x="40" y="357" font-size="15">Source + locks → Security CI → SBOM + signed release</text><text x="40" y="382" font-size="12">Local key signature proves integrity, not independent provenance.</text></g></svg>'''
(ROOT/'docs/dfd.svg').write_text(svg)

report=f'''# Term Project Report - Secure Build

## Cover

| Field | Value |
|---|---|
| Team name | {team['id']} |
| Members (name + ID) | {'; '.join(m['name']+' '+m['student_id'] for m in team['members'])} |
| Target application | Provided NoteVault, upgraded to {team['edition']} |
| Repository URL | {team['repository_url']} (private; instructor access must be granted) |
| Live application | {team['live_url']} |
| Date | 2026-09-04 |
| Team marker | {base['marker']} |
| Status | Evidence-backed implementation draft; team review and submission work remain |

## AI-tool usage disclosure

OpenAI Codex assisted with requirements review, implementation, tests, local vulnerability reproduction, build/security tooling and this report. Both teams received shared AI-assisted code in the same session. Different team names and markers do not make shared source independently authored. See docs/AI-DISCLOSURE.md. Students must disclose this assistance, independently reproduce and understand results, and confirm acceptance of the shared scaffolding with the instructor. No student authorship, weekly history or personal reflection is fabricated. The hosted CI result is linked to its GitHub run and recorded in evidence/hosted-ci.json.

## 1. Executive Summary

{team['id']} uses NoteVault as a local private notebook with account registration, sessions, owner-scoped notes and exports. Its {team['edition']} interface organizes notes into {', '.join(team['collections'])}. The assessment verified ten harmless baseline probes grouped into eight findings: two Critical, four High, and two Medium, using qualitative severity. The critical risks are shell injection and session forgery; authorization, SQL construction, interpreted content and password handling add further risk.

The new React/TypeScript client and Flask API remove the demonstrated mechanisms, retain legitimate application behavior and add persistent storage, conflict detection and reversible note removal. The security regression suite and frontend tests exercise both successful use and rejected attacks. Original source and actual probe outputs are retained. This draft does not claim a grade, independent team authorship, identity-stamped screenshots, or a completed live/video demo. The hosted Actions run is recorded as machine-generated evidence.

## 2. System Scope & Function

The application provides local account creation/sign-in, note creation/view/edit, literal search, collections, pin/archive/restore, CSV/JSON/text downloads, personal audit history, a protected team directory, and an administrator account listing without passwords. Notes remain private per user, even for administrators. Both teams use separate projects, databases, volumes, cookies and ports.

The original assessment target is lab/original/app.py from course revision 6996818be46cfb3f26b9b9d88e7c95af7ae32176. It is excluded from runtime/release packaging. scripts/reproduce_baseline.py loads it in a separate old-dependency environment and temporary SQLite database; it does not start a listener.

Data-flow diagram: docs/dfd.svg and docs/THREAT-MODEL.md. Trust boundaries separate the browser, Flask process, local database and build/release pipeline. The live deployment terminates HTTPS in Nginx and forwards only to loopback Gunicorn. Protected assets include private notes, password hashes, session tokens, audit records and release integrity. Real university services and real credentials are out of scope.

## 3. Threat Model - STRIDE (20 pts)

{stride}

### Ranked top risks

{risks}

Likelihood and impact are each ranked 1-5 to prioritize remediation. These are qualitative estimates, not formal CVSS calculations. Residual risk includes host compromise, database access by the operator, supply-chain trust and the explicitly enabled local demo accounts.

## 4. Vulnerability Findings (25 pts)

Run the steps in docs/BASELINE.md. Every probe is linked to the exact team marker and original-source digest in evidence/baseline.json. Only temporary fake data is used.

'''
for f in findings:
    fid,title,severity,cwe,owasp,endpoint,reproduction,impact,cause,mitigation,before,after,test,oldneedle,newneedle=f
    oldline=line('lab/original/app.py',oldneedle)
    report+=f'''### Finding {fid} - {title}

| Field | Value |
|---|---|
| CWE | {cwe} |
| OWASP 2025 | {owasp} |
| Severity | {severity} |
| Location | lab/original/app.py:{oldline}; {endpoint} |
| Evidence | evidence/baseline.json, finding {fid}, team marker {base['marker']} |

Reproduction: {reproduction}

Impact: {impact}

Root cause: {cause}

'''
report+='## 5. Remediation (25 pts)\n\n'
report+='The original source is preserved rather than rewritten. The application upgrade requested by the user is broader than a minimal patch; each security change below is tied to the specific unsafe mechanism. All listed fixes are in the actual AI-assisted remediation commit, not attributed to a student.\n\n'
for f in findings:
    fid,title,severity,cwe,owasp,endpoint,reproduction,impact,cause,mitigation,before,after,test,oldneedle,newneedle=f
    report+=f'''### Fix for {fid}

{mitigation}

```diff
- {before}
+ {after}
```

Commit: {fix}. Location: backend/app.py:{line('backend/app.py',newneedle)}{' and frontend/src/main.tsx' if fid=='F-04' else ''}.

Proof: {test}. See evidence/regression.xml and frontend/src/App.test.tsx. These tests verify the rejected attack and relevant legitimate behavior. Grading screenshots still need to be captured by the team with the required real identity/date stamp.

'''
python_count=count_components('sbom-python.json');js_count=count_components('sbom-frontend.json')
verification=(E/'cosign-verification.txt').read_text() if (E/'cosign-verification.txt').exists() else 'Verification has not been completed.'
container=json.loads((E/'container-check.json').read_text()) if (E/'container-check.json').exists() else None
scan=json.loads((E/'sca-container.json').read_text()) if (E/'sca-container.json').exists() else None
hosted_ci=json.loads((E/'verification-summary.json').read_text()).get('hosted_ci','Not recorded')
vulns=[v for r in scan.get('Results',[]) for v in r.get('Vulnerabilities',[])] if scan else None
report+=f'''## 6. Supply-Chain Hardening (15 pts)

Python dependencies and transitive dependencies are pinned with hashes in requirements.txt; the frontend uses package-lock.json and npm ci. The runtime is a minimal multi-stage image with pinned base-image digests, a non-root user, a read-only filesystem, dropped capabilities, no-new-privileges, resource limits and a separate data volume. Original vulnerable code, tests, local credentials and signing keys are excluded from the runtime image.

CycloneDX inventories: evidence/sbom-python.json contains {python_count} components; evidence/sbom-frontend.json contains {js_count} locked frontend and build components. This inventory includes development and platform-optional dependencies because the release contains the build source and lockfile. It includes React, React DOM, scheduler and Lucide, verified by the generation script; CI scans the full dependency set. The inventories describe application dependencies, not a claim of a full operating-system inventory.

Artifact: release/{team['slug']}-notevault.tar.gz. This is the hardened application/build source plus compiled browser bundle and application SBOMs. It is signed locally with Cosign; it is not a published container registry signature. release/SHA256SUMS and release/provenance.json record the artifact digest and input hashes. Private key material stays in ignored .keys/ and must never be shared. The verification bundle and public key are in release/.

Actual local verification output:

```text
{verification.strip()}
```

The local workflow intentionally uses a self-managed key without publishing to a transparency log; signature verification checks bytes against that public key, not the identity of the students. Keyless, transparency-backed signing is configured for a future tagged GitHub Actions run. No formal SLSA level is claimed: a locally generated manifest and signature do not independently attest to an isolated builder or reviewed source. The team must explain key custody and trusted verification inputs.

The initial Debian runtime image was rejected by the HIGH/CRITICAL gate. The current runtime uses a digest-pinned Alpine base; the original rejection is retained in evidence/container-base-rejected.json.

Container runtime verification: {('passed; non-root UID '+container['user']+', read-only root, loopback-only port and expected marker verified in evidence/container-check.json') if container else 'not yet recorded in evidence/container-check.json'}.

Container vulnerability scan: {str(len(vulns))+' HIGH/CRITICAL issues in the scanned image (see evidence/sca-container.json).' if vulns is not None else 'not yet completed; see the container scan log.'}

## 7. Security CI Pipeline (10 pts)

.github/workflows/security.yml installs hash-locked dependencies, runs backend and frontend regression tests, builds the client, runs Bandit SAST, pip-audit SCA, npm audit, Gitleaks secret scanning, a container scan and a real container health/configuration check. It produces SBOMs and release artifacts. Full commit hashes pin third-party Actions. Pull-request jobs have read-only repository access; only tagged release signing receives the OIDC permission it requires.

The SAST gate fails on HIGH findings at MEDIUM/HIGH confidence; pip-audit fails on any known Python vulnerability, npm audit fails at HIGH, the container gate fails on HIGH/CRITICAL, and Gitleaks fails on detected secrets. Tool failures are not treated as success. Historical intentionally vulnerable lab source is excluded from the hardened release scan and kept only for the assessment; generated packages, local state and evidence are also excluded from secret scans using the committed configuration.

Local pass evidence is in evidence/security-gate.json. scripts/prove_gate.py creates a temporary nonexecuted shell-injection fixture and confirms that the same Bandit threshold returns nonzero. The actual rejection is in evidence/gate-rejection.json. Hosted GitHub Actions status: {hosted_ci}. The intentional local failing-gate proof remains the negative control.

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

Flask test client and pytest reproduce and verify API behavior. React Testing Library/Vitest check rendering, saving and draft protection. Bandit, pip-audit, npm audit and Gitleaks generate scan reports. Docker builds the runtime; Trivy scans its packages; CycloneDX inventories dependencies; Cosign signs and verifies a local release. Full commands and scripts live in scripts/; original source is in lab/original/. The team marker is {base['marker']} and the baseline source digest is {base['baseline_sha256']}.

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
'''
(ROOT/'docs/REPORT.md').write_text(report)

# Render the same report into a clean, reviewable PDF with explicit draft status.
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether,Flowable
from reportlab.graphics.shapes import Drawing,Rect,String,Line,Polygon
styles=getSampleStyleSheet()
ink=colors.HexColor('#233b35' if team['theme']=='outsiders' else '#302c4d')
accent=colors.HexColor('#315444' if team['theme']=='outsiders' else '#62518d')
styles.add(ParagraphStyle(name='Body',fontName='Helvetica',fontSize=9.5,leading=14,spaceAfter=8,textColor=ink))
styles.add(ParagraphStyle(name='Section',fontName='Helvetica-Bold',fontSize=15,leading=19,spaceBefore=18,spaceAfter=10,textColor=accent,keepWithNext=True))
styles.add(ParagraphStyle(name='Sub',fontName='Helvetica-Bold',fontSize=11,leading=15,spaceBefore=12,spaceAfter=8,textColor=ink,keepWithNext=True))
styles.add(ParagraphStyle(name='Cell',fontName='Helvetica',fontSize=8,leading=11,textColor=ink))
styles.add(ParagraphStyle(name='CodeBlock',fontName='Courier',fontSize=7.5,leading=11,spaceAfter=10,backColor=colors.HexColor('#f2f4f3'),borderPadding=9))

def clean(s):
    return s.replace('’',"'").replace('“','"').replace('”','"').replace('–','-').replace('—','-').replace('→',' -> ').replace('×',' x ').replace('…','...')
def para(s,style='Body'):
    return Paragraph(html.escape(clean(s)).replace('\n','<br/>'),styles[style])

def diagram():
    d=Drawing(475,220)
    boxes=[(0,108,120,85,'TB1: Browser',['User / administrator','React interface']),
           (178,108,140,85,'TB2: App process',['Flask authorization','JSON / export']),
           (365,108,110,85,'TB3: Storage',['SQLite notes','Accounts / sessions']),
           (0,5,318,64,'TB4: Supply chain',['Source + locks -> CI -> SBOM + signature'])]
    for x,y,w,h,title,lines in boxes:
        d.add(Rect(x,y,w,h,rx=5,ry=5,fillColor=colors.HexColor('#f1f4f2'),strokeColor=accent,strokeDashArray=[3,2]))
        d.add(String(x+8,y+h-15,title,fontName='Helvetica-Bold',fontSize=8,fillColor=ink))
        for i,t in enumerate(lines):d.add(String(x+8,y+h-33-i*14,t,fontSize=8,fillColor=ink))
    for x1,y1,x2,y2 in [(120,155,178,155),(318,155,365,155),(247,69,247,108)]:
        d.add(Line(x1,y1,x2,y2,strokeColor=accent))
        if y1==y2:d.add(Polygon([x2,y2,x2-5,y2+3,x2-5,y2-3],fillColor=accent,strokeColor=accent))
        else:d.add(Polygon([x2,y2,x2-3,y2-5,x2+3,y2-5],fillColor=accent,strokeColor=accent))
    d.add(String(123,167,'JSON/CSRF',fontSize=6.5,fillColor=ink));d.add(String(320,167,'SQL',fontSize=6.5,fillColor=ink))
    d.add(String(0,207,'DATA FLOWS AND TRUST BOUNDARIES',fontSize=9,fontName='Helvetica-Bold',fillColor=accent))
    return d

story=[]
lines=report.splitlines();i=0
while i<len(lines):
    raw=lines[i];s=raw.strip()
    if not s:i+=1;continue
    if s.startswith('# '):
        story.append(para(team['id'].upper(),'Sub'));story.append(Paragraph('NoteVault<br/>Secure Build',ParagraphStyle('TitleCustom',fontName='Times-Roman',fontSize=34,leading=38,textColor=ink,spaceAfter=14)))
        story.append(para('IMPLEMENTATION REPORT DRAFT | '+team['edition'].upper(),'Sub'));i+=1;continue
    if s.startswith('## '):
        title=s[3:];story.append(para(title,'Section'));i+=1
        if title.startswith('3. Threat'):story.append(diagram())
        continue
    if s.startswith('### '):story.append(para(s[4:],'Sub'));i+=1;continue
    if s.startswith('```'):
        code=[];i+=1
        while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
        story.append(para('\n'.join(code),'CodeBlock'));i+=1;continue
    if s.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            parts=[c.strip() for c in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r'[-: ]+',c) for c in parts):rows.append([para(c,'Cell') for c in parts])
            i+=1
        widths={2:[105,370],3:[105,100,270],4:[45,132,90,208]}.get(len(rows[0]),[475/len(rows[0])]*len(rows[0]))
        table=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e8eeea')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.35,colors.HexColor('#d4ded8')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
        story.extend([table,Spacer(1,10)]);continue
    content=[]
    while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','|','```')):
        content.append(lines[i]);i+=1
    if not content:i+=1;continue
    story.append(para('\n'.join(content)))

out=ROOT/'output/pdf';out.mkdir(parents=True,exist_ok=True)
filename=out/(team['slug']+'-report-draft.pdf')
def page(canvas,doc):
    canvas.saveState();canvas.setStrokeColor(colors.HexColor('#dbe2dd'));canvas.line(60,48,535,48)
    canvas.setFillColor(ink);canvas.setFont('Helvetica',8);canvas.drawString(60,35,team['id']+' | NoteVault | Draft for team review')
    canvas.drawRightString(535,35,str(doc.page));canvas.restoreState()
SimpleDocTemplate(str(filename),pagesize=(595.28,841.89),leftMargin=60,rightMargin=60,topMargin=45,bottomMargin=62,title=team['id']+' - NoteVault Secure Build Draft',author='AI-assisted draft; team review pending').build(story,onFirstPage=page,onLaterPages=page)
print(filename)
