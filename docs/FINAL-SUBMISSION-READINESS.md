# Final submission readiness — Team Outsiders

Deadline: **Friday, November 6, 2026 at 16:59 Asia/Bangkok**.

This checklist separates verified repository evidence from human actions that cannot be inferred or completed on a student's behalf.

## Verified technical package

- [x] Eight findings reproduced with harmless local probes and exact request/response evidence.
- [x] Findings mapped to root causes, CWE, OWASP, impact, fixes, commits, and regression tests.
- [x] 25 backend tests and 3 frontend tests pass; the production frontend builds.
- [x] Bandit, pip-audit, npm audit, Gitleaks, and the HIGH/CRITICAL container gate pass.
- [x] Hardened container is non-root, read-only, capability-dropped, health-checked, and loopback-bound.
- [x] CycloneDX inventories, artifact digest, provenance, local Cosign verification, and tamper rejection are retained.
- [x] Node2Shell applicability reviewed: build pinned to fixed Node 24.22.1; Node absent from final runtime.
- [x] PHP2Shell applicability reviewed: no PHP or Composer surface exists; not applicable and not counted as a finding.
- [x] Repository and live application URLs are on the report cover.
- [x] AI assistance and shared scaffolding are disclosed; no student work or contribution is fabricated.

## Student actions required before portal upload

- [ ] Zaw Win Htut independently reviews the report, reproduces the selected demo sequence, and confirms every claim understood.
- [ ] Wanna San independently reviews the report, reproduces the selected demo sequence, and confirms every claim understood.
- [ ] Myo Zin Thant independently reviews the report, reproduces the selected demo sequence, and confirms every claim understood.
- [ ] Replace the cover's “Not supplied” demo value with a viewable unlisted YouTube or Drive URL; test it while signed out.
- [ ] Record real member work/review in `docs/WEEKLY-LOG.md`; do not backfill invented dates or contributions.
- [ ] Confirm the instructor can open the private repository and confirm acceptance of the shared AI-assisted scaffold.
- [ ] Each student submits a truthful private peer rating (Full / Most / Some / Little) with a one-line reason.
- [ ] One representative obtains the private **term-project** submission code, uploads the final PDF, and saves the portal receipt.
- [ ] Follow `docs/SEVEN-PHASE-TEAM-HANDOFF.md`: create the final private repository under a verified Team Outsiders identity, preserve history, add all members/instructor, update `team.json`, rerun CI, and rebuild the report.
- [ ] Each member completes `docs/STUDENT-REFLECTIONS.md` personally and submits `docs/PEER-FEEDBACK-TEMPLATE.md` privately.

## Five-minute pre-upload review

1. Open both repository and demo links from a signed-out/private browser window.
2. Check that the PDF cover has the correct three names/IDs, repository URL, live URL, demo URL, and team marker.
3. Show attack → root cause → fix → retest for F-02, plus one of F-01 or F-05.
4. Explain the failing-gate negative control, current zero-known-issue scan result, SBOM, and signature limitation.
5. Explain that Node2Shell is patched at build time and absent at runtime, while PHP2Shell is out of scope because there is no PHP surface.
6. Upload before the deadline and retain the receipt. A ZIP or local PDF is not proof of submission.
