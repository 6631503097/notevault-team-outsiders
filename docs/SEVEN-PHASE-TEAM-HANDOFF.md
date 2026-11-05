# Team Outsiders — seven-phase ownership and submission handoff

Deadline: **Friday, 6 November 2026 at 16:59 Asia/Bangkok**.

Members:

- Zaw Win Htut — 6631503101
- Wanna San — 6631503097
- Myo Zin Thant — 6631503076

The existing `Thiha-Lynn/notevault-team-outsiders` repository is a private staging/handoff source. The final repository must be created under a verified Team Outsiders member or a team-owned GitHub organization. Do not guess usernames, reuse Team Imposters identities, rewrite the AI-assisted history as student work, or claim tasks that students did not perform.

## Information the team must supply first

```text
FINAL_REPOSITORY_OWNER_GITHUB=
ZAW_GITHUB=
WANNA_GITHUB=
MYO_GITHUB=
INSTRUCTOR_GITHUB=
ZAW_GIT_EMAIL=
WANNA_GIT_EMAIL=
MYO_GIT_EMAIL=
```

Each account holder must verify their own username and choose a Git email that GitHub associates with that account. A GitHub no-reply email is acceptable. Never share passwords, personal access tokens, recovery codes, SSH private keys, or submission codes with teammates or an AI assistant.

## Phase 1 — identity, repository ownership, and clean handoff

**Goal:** establish a private repository owned by the actual team and preserve the complete disclosed history.

1. Elect one verified member account or a Team Outsiders organization as owner.
2. On that owner's authenticated machine, clone `Team_Outsiders_Repository.bundle` from the handoff ZIP:

```sh
git clone Team_Outsiders_Repository.bundle notevault-team-outsiders
cd notevault-team-outsiders
git switch remediation
git remote remove origin
```

3. Verify that the history contains the original course baseline and the `Codex (AI-assisted implementation) <codex@local.invalid>` commits. Do not rewrite those authors as students.
4. Authenticate interactively:

```sh
gh auth login
gh auth status
```

5. Create and push the new private repository. Replace only the owner placeholder:

```sh
OWNER="FINAL_REPOSITORY_OWNER_GITHUB"
REPO="notevault-team-outsiders"
gh repo create "$OWNER/$REPO" --private --source=. --remote=origin --push
git push -u origin remediation
gh repo edit "$OWNER/$REPO" --default-branch remediation
```

6. Add the other two verified student accounts and the verified instructor account. Student collaborators need `push`; instructor access normally needs `pull` unless the instructor requests otherwise:

```sh
gh api -X PUT "repos/$OWNER/$REPO/collaborators/ZAW_GITHUB" -f permission=push
gh api -X PUT "repos/$OWNER/$REPO/collaborators/WANNA_GITHUB" -f permission=push
gh api -X PUT "repos/$OWNER/$REPO/collaborators/MYO_GITHUB" -f permission=push
gh api -X PUT "repos/$OWNER/$REPO/collaborators/INSTRUCTOR_GITHUB" -f permission=pull
gh api "repos/$OWNER/$REPO/invitations"
```

Do not invite the repository owner as a collaborator. Each invitee must accept. Verify access by having each person open the private repository while signed into the intended account.

7. Update `team.json` `repository_url` to the observed new HTTPS URL. Rebuild the report; do not hand-edit only the PDF.
8. Every student configures identity only on their own clone:

```sh
git config user.name "ACTUAL STUDENT NAME"
git config user.email "VERIFIED GITHUB EMAIL"
git config --get user.name
git config --get user.email
```

**Exit gate:** new private repository exists under a verified Outsiders identity, all three students and instructor can open it, the `remediation` branch and full history are present, and `team.json` points to it.

## Phase 2 — threat model and safe baseline verification (20 points)

**Goal:** each member understands the system boundary and independently confirms at least one harmless baseline behavior.

1. Read `docs/THREAT-MODEL.md`, `docs/dfd.svg`, `docs/BASELINE.md`, and findings F-01–F-08 in `docs/REPORT.md`.
2. Use only the isolated test-client harness from `docs/BASELINE.md`; never expose the historical vulnerable app publicly.
3. Check the four trust boundaries: browser, Flask process, SQLite storage, and build/release pipeline.
4. Confirm the STRIDE table, ranked risks, assets, attackers, mitigations, and residual risks match the actual code.
5. Each student records the date, exact command, observed result, and explanation in `docs/WEEKLY-LOG.md`.

Suggested real review split, which the team may adjust:

- Zaw: DFD/STRIDE and F-02 owner-boundary reproduction.
- Wanna: F-01 SQL injection and F-05 command injection reproduction.
- Myo: F-07 session forgery, release boundary, and residual-risk review.

**Exit gate:** one teammate reviews another's explanation, evidence uses the Team Outsiders marker, and no Team Imposters screenshot or marker is present.

## Phase 3 — vulnerability findings and evidence (25 points)

**Goal:** validate the eight report findings as complete security arguments.

For every finding F-01–F-08, verify:

- affected endpoint/location;
- harmless reproduction steps and exact observed result;
- impact without exaggeration;
- root cause;
- severity rationale;
- CWE and OWASP mapping;
- retained evidence path;
- correct Team Outsiders marker.

Capture identity/date-stamped screenshots showing the full command or browser URL, readable result, student's name/ID, timezone, and team marker. Minimum recommended captures are F-02 before/after, one injection before/after, passing tests/gate, hosted Actions, and SBOM/signature verification.

**Exit gate:** the report makes no unsupported RCE, browser-alert, administrator-identity, student-authorship, or screenshot claim.

## Phase 4 — remediation and regression proof (25 points)

**Goal:** demonstrate that each fix addresses its root cause while preserving legitimate behavior.

1. Run backend and frontend tests:

```sh
PYTHONPATH=. .venv/bin/pytest -q
npm --prefix frontend test -- --run
npm --prefix frontend run build
```

2. Trace F-02 to owner-scoped SQL, F-01 to bound parameters, F-05 to complete shell removal, F-07 to opaque revocable sessions, and F-08 to CSRF/origin controls.
3. Each student performs one genuine documentation or evidence improvement on a personal branch and opens a PR:

```sh
git switch -c review/STUDENT-FIRSTNAME-finding
# Edit only verified review/evidence/reflection files.
git add docs/ evidence/
git commit -m "docs: record STUDENT-NAME review of F-XX"
git push -u origin HEAD
gh pr create --base remediation --fill
```

Another teammate reviews the PR. Do not create empty or duplicate commits just to manufacture contribution history.

**Exit gate:** 25 backend tests and 3 frontend tests pass, the production build passes, each personal commit corresponds to real review work, and PR review is genuine.

## Phase 5 — supply-chain and release hardening (15 points)

**Goal:** reproduce the dependency, container, SBOM, provenance, and signature evidence.

```sh
./scripts/verify.sh
./scripts/sbom.sh
.venv/bin/python scripts/package_release.py
.venv/bin/python scripts/sign_local.py
.venv/bin/python scripts/container_check.py
```

Verify zero known Python/npm audit findings, zero HIGH/CRITICAL final-container findings, non-root/read-only/capability-dropped controls, both CycloneDX inventories, the release SHA-256, valid signature, and tamper rejection. Explain that a local key signature checks artifact integrity but not independent student identity or formal SLSA provenance.

Node2Shell is addressed by the patched Node 24.22.1 build pin and Node's absence from the final runtime. PHP2Shell is not applicable because no PHP surface exists.

**Exit gate:** generated evidence is current on the team's machine, private keys and local databases are untracked, and no secret appears in Git history.

## Phase 6 — hosted CI and repository evidence (10 points)

**Goal:** prove that the new team-owned repository enforces the security gates.

1. Push the reviewed commits to `remediation` and watch `.github/workflows/security.yml`.
2. Confirm the hosted run includes tests, Bandit, pip-audit, npm audit, Gitleaks history scan, deliberate HIGH rejection, container build/scan/smoke test, SBOM, and release artifact.
3. Save the exact run URL and head SHA in `evidence/hosted-ci.json` and `evidence/verification-summary.json`.
4. Rebuild the report after changing the repository URL and hosted-run evidence:

```sh
.venv/bin/python scripts/build_report.py
```

**Exit gate:** Actions is green on the final team-owned commit, report links resolve for the instructor, and no old `Thiha-Lynn` repository URL remains in the final report.

## Phase 7 — presentation, peer feedback, reflections, and submission (5 points + required administration)

**Goal:** produce attributable human review and the actual submission.

1. Each member personally completes `docs/STUDENT-REFLECTIONS.md` after reproducing evidence.
2. Each member privately completes `docs/PEER-FEEDBACK-TEMPLATE.md`; do not commit completed ratings unless the instructor explicitly requires it.
3. Record a 7–10 minute demo using `docs/DEMO.md`: attack → root cause → fix → retest, then CI/SBOM/signature/residual risks.
4. Upload as unlisted YouTube or viewable Drive, and test the link while signed out.
5. Put the real demo URL and new repository URL into `team.json`/the report source, rebuild the PDF, and visually inspect every page.
6. Confirm the instructor accepts the disclosed shared AI-assisted scaffold.
7. Use the private term-project code at `https://learn.zcr.ai/submit`; never commit or publish the code.
8. Upload before the deadline and save the receipt outside the repository.

**Exit gate:** all three members can answer unscripted viva questions, private ratings are complete, the PDF cover has working repository/live/demo links, and a portal receipt exists.

## Final non-negotiable checks

- The repository belongs to a verified Outsiders identity, not Team Imposters.
- `team.json` contains exactly the three Outsiders names/IDs above.
- The final report contains no Team Imposters names, marker, screenshots, or URLs.
- AI-assisted commits remain disclosed and are not rewritten as student-authored.
- Each student contribution is an actual review/evidence/demo/submission action.
- Private keys, tokens, codes, peer-rating explanations, live databases, and `.env` files are not committed.
