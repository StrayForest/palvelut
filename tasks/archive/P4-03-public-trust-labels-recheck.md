# P4-03 — Public trust labels and re-check expiry queue

Completed the active P4 build step: public verification surfaces now explain factual trust semantics, show the exact verification fact/source/date, and expired latest checks feed a deterministic re-check queue.

## What changed

- Added a locale-aware public `/palvelut/{locale}/trust/` explanation defining the narrow meaning of verification labels and explicitly excluding service-quality ratings or unnamed licence claims.
- Added exact public profile labels such as `Y-tunnus found in PRH YTJ Open Data API v3 · checked YYYY-MM-DD`, with official-source links.
- Public labels expose only currently valid `verified` facts and hide expired checks.
- Added `recheck_expiry_queue()` over the existing `expires_at` field: only expired latest verified facts are due; any newer same-kind check suppresses duplicate re-check work.
- Added deterministic regression coverage for exact wording/date/source, expiry hiding/queueing, newer-check suppression, and public profile/trust surfaces.
- Kept already completed adapter/registry work in P4-01/P4-02; this closeout does not duplicate those steps.

## Evidence

- Implementation exact head: `744d90e4a759cdb841c3263042b559a43977cc99`.
- GitHub Actions `Compose stack` run `33960076779`: PASS on the exact implementation head, including lint/format, type check, dependency/secret scans, migrations, non-browser/browser gates and disposable smoke.

## Deviations

None.
