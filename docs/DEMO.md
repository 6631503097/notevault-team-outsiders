# Demo runbook

This is a script for the teams to perform, not a claim that a demo has happened.

1. State the exact team name and show `/api/config` with its marker. Log in as Alice; create, search, pin, edit, archive and restore a note; show a real downloaded export.
2. Open `evidence/baseline.json`, then reproduce the local baseline using `docs/BASELINE.md`. Explain the F-02 owner-boundary failure and show the administrator's marker read by Alice in the old application.
3. Run the F-02 regression test in `tests/test_security.py`. Explain the `WHERE id=? AND owner_id=?` predicate; demonstrate successful access to Alice's own note and a 404 for the administrator's note.
4. Choose F-01 or F-05. Explain parameterized SQL or the removal of shell execution. Show the harmless before-probe and passing after-test.
5. Show `evidence/gate-rejection.json`, run `scripts/prove_gate.py`, and explain why a scanner must return nonzero on a HIGH finding. This deliberate local negative control is the failure evidence; do not mislabel it as a hosted workflow failure.
6. Show the CycloneDX component inventory, release digest and Cosign verification. Explain the distinction between a local key signature and identity-backed provenance.
7. End with residual risks and a real contribution summary from each member.
8. If asked about current advisories, explain that Node2Shell is patched by the Node 24.22.1 build pin and Node is absent from the final runtime; PHP2Shell is not applicable because the project has no PHP surface. Neither is presented as a ninth NoteVault finding.

Week 16: perform the work-in-progress walkthrough and collect actual peer feedback. Week 19: record and submit the walkthrough before the session; prepare for the three-minute live Q&A. Each member should explain owner authorization, CSRF, password storage, session revocation, the build gate, and why signing alone does not prove software is secure.

For grading screenshots, use the required real terminal identity/date stamp beside the actual result and capture it yourself. Browser-only captures made during implementation do not replace the required identity-stamped screenshots.
