# Wanna San - guided review of F-01 and F-05

Prepared for Wanna San (6631503097), Team Outsiders / Fieldnotes. This is an AI-assisted technical review draft, not a signed personal reflection. The original implementation and fixes were inherited; this branch does not claim that Wanna implemented them.

## What the assistant prepared and ran

The assistant prepared scripts/capture_f01_f05.py and the technical notes below. The JSON/log files identify the automated operator, source hashes, source head, actual timestamp and observed HTTP results. The harness uses only temporary SQLite databases and Flask test clients; no network listener is opened. No session/CSRF token values are retained.

- Baseline capture: ../evidence/review-wanna-f01-f05/baseline.json
- Patched capture: ../evidence/review-wanna-f01-f05/patched.json
- Focused regression output: ../evidence/review-wanna-f01-f05/regression.log
- Regression XML: ../evidence/review-wanna-f01-f05/regression.xml

Wanna must inspect these outputs, personally reproduce the assigned checks, and describe the actions she actually performed. Assistant-run results are not identity-stamped student screenshots.

## F-01 - SQL injection (CWE-89; OWASP A05:2025)

The original login and search interpolate input into SQL source. A quote/comment sequence can change the query's grammar. The harmless baseline checks an injected login with an incorrect fixture password and a search that exposes the other owner's team marker. A session cookie being issued for the injected login is not, by itself, proof that it is a normal administrator identity.

The patched login binds the username with a placeholder and checks the stored password hash separately. The search also binds input, escapes LIKE wildcards for literal searching, and includes owner_id in the query. Parameter binding prevents syntax injection; owner scoping enforces which account's data can be returned. They solve different problems.

Read the actual source:

- Original login: ../lab/original/app.py (login route)
- Original search: ../lab/original/app.py (search route)
- Patched login: ../backend/app.py#L246
- Patched owner-scoped literal search: ../backend/app.py#L277
- Regression: ../tests/test_security.py#L47

Review the captures for these results: baseline injected login issues a cookie; the injected search includes the administrator note's Team Outsiders marker. In the patched app, the injected login returns 401, the same search returns no notes, and a legitimate search for a newly created own note still succeeds. The JSON files, rather than this summary, record the actual observations.

## F-05 - command injection in export (CWE-78; OWASP A05:2025)

The original export appends fmt to a command executed through a shell. A semicolon can start another command. The baseline uses only `txt; printf NV_SAFE_PROBE`; the marker proves the extra harmless command ran. This is not evidence of a root shell, host takeover or an attack on the live deployment.

The patched export has no shell execution. It accepts only json, csv or txt and serializes owned notes directly in Python. This removes the unsafe interpreter boundary instead of trying to filter a list of dangerous characters. Owner scoping also prevents export of another user's notes.

Read the actual source:

- Original export: ../lab/original/app.py (export route)
- Patched export and allowlist: ../backend/app.py#L343
- Rejected-format regressions: ../tests/test_security.py#L79
- Legitimate note lifecycle and all three exports: ../tests/test_security.py#L26

Review the captures for these results: the baseline contains NV_SAFE_PROBE; the patched app returns 400 for that malformed format and the other invalid formats. Valid JSON, CSV and text exports return 200 with the harmless own-note fixture and attachment headers.

## What Wanna must personally do

On your own clone, check out this branch, inspect the source and results, and run the following commands yourself. Use the environments documented in docs/BASELINE.md and the README; do not start the vulnerable Compose app.

```sh
set -o pipefail
printf 'Wanna San | 6631503097 | Team Outsiders\n'
date '+%Y-%m-%d %H:%M:%S %z'
.lab-venv/bin/python scripts/capture_f01_f05.py --mode baseline --operator-label 'Wanna San - personally invoked' --summary | tee evidence/review-wanna-f01-f05/baseline.log
PYTHONPATH=. .venv/bin/python scripts/capture_f01_f05.py --mode patched --operator-label 'Wanna San - personally invoked' --summary | tee evidence/review-wanna-f01-f05/patched.log
PYTHONPATH=. .venv/bin/pytest -q tests/test_security.py -k 'f01 or f05 or legitimate_note_lifecycle_and_exports' --junitxml=evidence/review-wanna-f01-f05/regression.xml | tee evidence/review-wanna-f01-f05/regression.log
.venv/bin/python scripts/capture_f01_f05.py --refresh-manifest
```

These commands intentionally replace this branch's automated captures with the results from your own invocation. The source/operator/timestamp metadata must remain truthful. Capture readable screenshots of the full commands and results; include your actual name/ID, date/time/timezone and Team Outsiders marker. Do not reuse another member's screenshot or relabel an assistant-generated capture as your independent work.

## Personal explanation - draft supplied by Wanna during the guided review

Before completing your section in docs/STUDENT-REFLECTIONS.md, answer:

1. Why do SQL placeholders stop syntax injection, and why is an owner check still necessary?
2. Why is removing the shell a stronger fix than filtering command characters? Which export formats still work?
3. What did you personally read, run, inspect or change? Distinguish assistant-run checks from your own actions.
4. What limitation or residual risk did you identify? Do not claim to have tested a risk you only reasoned about.
5. What did you learn or what would you do differently?

No personal learning statement, signature or yes/no attestation is supplied on your behalf. Commit your actual evidence/reflection yourself with your verified Git identity and retain the AI disclosure. Another teammate should submit a substantive review before the PR is marked ready and merged.

### Wanna's supplied review activity and limitation

The following is Wanna's own wording supplied in this conversation, formatted by the assistant:

> So far, I have reviewed the code, vulnerability explanations, and remediation patches. One limitation I noticed is that while parameterized queries prevent SQL injection, they do not inherently restrict data access boundaries—requiring explicit authorization and owner checks to be enforced alongside parameterized queries.

This supports a claim of source/explanation review. It does not state that Wanna personally invoked the reproduction or regression commands.

### Technical points to confirm before signing the reflection

- Wanna explained that untrusted quotes or OR expressions can alter SQL built through concatenation, and distinguished bound values from authorization. Bound placeholders protect the values supplied through them; they do not make every possible dynamically constructed SQL component safe. This app's ownership column is owner_id.
- Wanna's first F-05 explanation described a general shell=False subprocess alternative. That is not this app's implementation: export removes subprocess entirely and serializes owned notes in Python after an allowlist check. Wanna subsequently corrected this in her own words: the fix eliminates external subprocess and shell execution. The assistant clarified that TXT is built by string joining and returned in memory; no export file is written.
- Personal reproduction screenshots, exact personal run time, chosen Git email, name/date signature and final yes/no attestation remain for Wanna to provide herself.

### Wanna's F-05 correction and current activity

Wanna clarified that the export fix eliminates external subprocess/shell execution and uses Python serialization instead. She explicitly stated: "So far, I have only reviewed the code and results." Her draft reflection preserves that limit. Personal reproduction/screenshots and final signature remain pending; they are not inferred from this PR or from the assistant's automated captures.
