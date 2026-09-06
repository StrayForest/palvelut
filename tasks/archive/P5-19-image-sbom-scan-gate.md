# P5-19 — Image/SBOM scan gate

Completed the next active P5 gate: the production image CI now generates an SPDX JSON SBOM from the exact locally built application image and scans that same image for fixed critical vulnerabilities before publication.

## Verification

- `Production image` now runs on pull requests so the image gate is exercised before merge; the GHCR push step remains skipped for pull-request runs.
- The image reference is canonicalized once with a lowercase GHCR owner and reused for build, SBOM generation, vulnerability scan and publication.
- SBOM generation uses `anchore/sbom-action` pinned to full commit `3ad7283483fc7af8ff2b4ea19663c2d5ca935e26` (`v0.24.2`) and uploads an SPDX JSON artifact with 14-day retention.
- Vulnerability scanning uses `anchore/scan-action` pinned to full commit `27805bf3b4e84b4a5c980df22ed233c00390a439` (`v7.4.2`) and fails on fixed critical vulnerabilities.
- Exact pre-archive head `b2958f54229b6c75a5c233f2c48b4f8980c64e4c` passed `Production image` run `34014384600`; image build, SBOM generation and vulnerability scan all completed successfully.
- The first implementation run exposed a mixed-case GHCR reference mismatch before scanning; the canonical reference fix was applied and the subsequent exact-head run passed.

## Deviations

None.
