# P4-09 — Accessibility acceptance

Completed the active P4 acceptance criterion: the public surfaces pass the WCAG 2.2 AA accessibility checklist covered by the repository browser gate.

## Verification

- Public home, search, trust and privacy surfaces expose the expected document language, a single main landmark and a single H1.
- Interactive controls have accessible names, and positive `tabindex` values are rejected.
- Keyboard-only navigation reaches the skip link, moves focus to main content and continues through the page.
- The public home remains usable at 200% text zoom without horizontal clipping at the acceptance viewport.
- Reduced-motion preference does not block public navigation.
- Existing canonical browser coverage continues to exercise 360 px and 1440 px layouts, skip-link focus and console/page-error cleanliness.

## Evidence

- Accessibility verification exact head: `9c72c82301e47e36ffa9aec0c938477784ba4d93`.
- GitHub Actions `Compose stack` run `33972062485`: PASS on the exact verification head, including lint/format, type check, dependency/secret checks, builds, migrations, provider security/integration, canonical non-browser/browser gates, Playwright evidence and disposable smoke.

## Deviations

- The repeatable CI gate validates rendered semantics, accessible names, keyboard behavior, zoom/reflow and reduced-motion behavior. A physical assistive-technology session is not available in CI, so no claim is made that an external screen-reader binary was exercised.
- The separate public legal/controller/contact acceptance criterion remains active because it requires owner/legal review.
