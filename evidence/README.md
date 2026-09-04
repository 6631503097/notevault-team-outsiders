# Evidence index

All data here comes from actual local execution, except explanatory metadata clearly identified as such. The main verification index is `verification-summary.json`.

- `baseline.json`: ten harmless reproduced probes against a fresh temporary instance of the original starter, with the exact team marker and source digest.
- `regression.xml`, `verification.log`: backend and frontend tests, production frontend build, security gates and the deliberately rejected SAST fixture.
- `sast.json`, `sca-python.json`, `sca-npm.json`, `secrets.json`, `secrets-history.json`: scanner outputs for the hardened code/dependencies and repository history.
- `container-base-rejected.json`: the original Debian base failed the HIGH/CRITICAL gate; it was replaced, without suppressing its findings.
- `sca-container.json`, `container-check.json`: the final image scan and effective non-root, read-only, isolated container settings.
- `gate-rejection.json`: nonzero SAST result from a nonexecuted high-severity test fixture. This is not a hosted Actions result.
- `sbom-python.json`, `sbom-frontend.json`: application Python and full locked frontend/build CycloneDX inventories; the latter includes development and optional dependencies.
- `cosign-verification.txt`, `cosign-tamper-rejection.txt`: the actual release verifies; a byte-modified copy is rejected. Local key signing has no public transparency record and claims no SLSA level.

The signed release, bundle, digest and public key are under `release/`. Never share `.keys/`, `.venv/`, `.lab-venv/` or the live databases. These machine results do not replace the course's required student identity-stamped screenshots, actual contribution records or demo.
