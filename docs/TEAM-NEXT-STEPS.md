# Team Outsiders - remaining personal work

Deadline: Friday 6 November 2026, 16:59 Asia/Bangkok. This is a task list, not a record that anyone has done the work.

Suggested split (confirm together):

- Zaw Win Htut (6631503101): review DFD/STRIDE and F-02 owner isolation; reproduce before/after; explain the owner predicate and one residual risk.
- Wanna San (6631503097): review F-01 SQL injection and F-05 export command injection; reproduce harmless baseline and patched rejection; explain bound parameters and shell removal.
- Myo Zin Thant (6631503076): review F-07 opaque sessions, logout/expiry/forgery tests, SBOM and signature limitations; explain build/runtime advisory applicability.

Each person must use their own clone, confirm their own GitHub-linked Git email, and configure identity locally. Do not copy another person's evidence or commit another person's reflection.

1. Clone https://github.com/6631503097/notevault-team-outsiders and switch to remediation.
2. Read docs/AI-DISCLOSURE.md, docs/BASELINE.md, docs/THREAT-MODEL.md and assigned findings in docs/REPORT.md. Use only the no-listener baseline harness; never publicly serve lab/original.
3. Personally run the assigned reproduction and corresponding regression test. Capture exact commands/results with your name/ID, actual date/time/timezone and Team Outsiders marker. Include a screenshot of the deliberate HIGH-severity rejection (scripts/prove_gate.py and evidence/gate-rejection.json), plus passing CI and SBOM/signature evidence. A failed infrastructure-only CI run is not proof of a HIGH finding rejection. Do not label automated outputs as student screenshots.
4. Create a useful evidence/documentation improvement on a personal review branch. Record actual work in docs/WEEKLY-LOG.md and personally fill your own section of docs/STUDENT-REFLECTIONS.md.
5. Commit only real work using your verified identity. Push and open a PR to remediation; another teammate must read and genuinely review it. Suggested review cycle: Zaw reviews Wanna, Wanna reviews Myo, Myo reviews Zaw.
6. Rehearse and record docs/DEMO.md together: attack -> code root cause -> fix -> retest, then CI, SBOM/signature and residual risks. Upload to unlisted YouTube or viewable Drive; test while signed out. Supply only the public viewing URL.
7. Privately submit Classroom peer feedback for every member including self (Full/Most/Some/Little plus one truthful line). Never commit completed ratings or explanations.

Team owner: resolve instructor access (read-only invitation was rejected on the personal repository; write invitation requires an explicit choice). Confirm instructor acceptance of the disclosed shared AI-assisted scaffold. After merging reviews, rerun CI and regenerate the report with the actual demo URL; inspect the PDF together. Obtain the private term-project code yourself, upload the final PDF through the portal, and retain the receipt outside Git. Never send the private code or login credentials to the assistant.

No student contribution, reflection, instructor acceptance, private rating, demo upload or portal receipt can be truthfully completed by an assistant on your behalf.
