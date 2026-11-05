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
