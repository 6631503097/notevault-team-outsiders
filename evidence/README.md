# Evidence scopes

Use docs/EVIDENCE-PROVENANCE-AUDIT.md and evidence/audit/provenance.json to determine what supports the corrected report.

- audit/baseline.json and audit/execution-journal.json: independently run local checks with exact command, timestamp, exit code and output hashes.
- audit/ci/: only outputs rewritten by observed steps in the recorded team-owned GitHub Actions run. Other files uploaded alongside them are not automatically fresh evidence.
- Root-level student screenshots and baseline.json: member-submitted material, with their own authorship and limitations. They are not assistant screenshots.
- Other root-level legacy files: retained history or earlier checks; they are not cited by the corrected PDF merely because they exist. The curated audited ZIP omits uncited legacy evidence from its active source tree.

The full-history bundle preserves prior material honestly. Neither an empty report nor a team marker proves freshness or independent authorship. Local keys and databases remain private and excluded. Personal ratings and portal codes must never be committed.
