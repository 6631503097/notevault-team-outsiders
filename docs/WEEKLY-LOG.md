# Weekly investigation and contribution log

No retrospective weekly work is claimed. Record actual dates, authors, reviewed changes, and evidence as the term proceeds.

| Week/topic | Finding or question | Investigator | Reviewer | Evidence | Commit | Outcome |
|---|---|---|---|---|---|---|
| 4 - injection | F-01, F-05 | To be recorded | To be recorded | Local implementation probes exist; student reproduction pending | To be recorded | Pending team review |
| 5 - client-side injection | F-04 | To be recorded | To be recorded | Student browser evidence pending | To be recorded | Pending team review |
| 6 - authentication/authorization | F-02, F-03, F-07, F-08 | To be recorded | To be recorded | Student reproduction pending | To be recorded | Pending team review |
| 6 - auth (session forgery) | F-07 | Myo Zin Thant (6631503076) | pending teammate review | evidence/baseline.json F-07 (marker 3d821afbe8a0) + evidence/wk6-f07-myo.png; GET /admin → 200 | branch review/myo-f07 | Reproduced: forged admin session via source SECRET; admin hash dumped |
| 6 - auth (object-level authz) | F-02 | Zaw Win Htut (6631503101) | pending teammate review | docs/REVIEW-ZAW-F02.md; evidence/f02-before-zaw-2026-11-05.png; evidence/f02-after-zaw-2026-11-05.png (marker 3d821afbe8a0) | branch review/zaw-f02 | Reproduced: alice reads the administrator note (HTTP 200); after the fix the same read and write are 404 and the regression test passes. DFD/STRIDE claims re-checked against code; residual risk recorded (per-query predicates, no central policy) |
| 10 - API security | Cross-owner writes; mass assignment | To be recorded | To be recorded | Tests included | To be recorded | Pending team review |
| 12 - supply chain | Dependency scan, SBOM and signatures | To be recorded | To be recorded | Local artifacts generated | To be recorded | Pending team review |
| 13 - containers | Non-root/read-only deployment | To be recorded | To be recorded | Runtime inspection | To be recorded | Pending team review |
| 15 - DevSecOps | Gate fail/pass demonstration | To be recorded | To be recorded | Hosted CI evidence pending | To be recorded | Pending team review |

Record each member's actual contribution privately at the end using the instructor's peer-rating procedure. Membership is not proof of contribution.
