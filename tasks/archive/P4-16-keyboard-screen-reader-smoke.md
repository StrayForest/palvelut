# P4-16 — Keyboard and screen-reader smoke

Completed the remaining active P4 gate: focused keyboard and screen-reader-facing browser smoke coverage.

## Verification

- Public home, search, trust and privacy surfaces expose one main landmark and one level-one heading through browser accessibility roles.
- Axe runs against WCAG 2 A/AA, 2.1 A/AA and 2.2 AA tags; critical and serious violations fail the smoke.
- Keyboard-only traversal of the public search form follows service → city → search in DOM order, and Enter submits the form to a usable results page.
- This is intentionally narrower than P4-09: that archived step covers the broader accessibility acceptance checklist, while this step adds the explicit repeatable keyboard/screen-reader-facing smoke gate.

## Evidence

- Verification exact head: `1a76feaf6de35cb1ab9ab097eef99c7d17cfe7d0`.
- GitHub Actions `Compose stack` run `33997601178`: PASS on the exact verification head, including lint/format, type check, dependency/secret checks, builds, migrations, provider security/integration, canonical non-browser/browser gates, Playwright evidence and disposable smoke.

## Deviations

- CI exercises the browser accessibility tree, ARIA roles/names and axe rules rather than launching an external desktop screen-reader binary. The smoke therefore guards screen-reader-facing semantics deterministically without claiming product-specific NVDA, VoiceOver or Orca compatibility.
