# P0-06 — I18n skeleton and accessible base layout

Completed: 2026-09-03
Implementation head: `fee6e623aff1f90b6d600c50a923adcf8a5ae26e`; PR #9

## Scope

- Configured Django UI locales in RU/FI/EN order and enabled `LocaleMiddleware`.
- Added the project-level template and locale catalog roots.
- Added an accessible base template with document language propagation, viewport metadata, skip link, labelled primary navigation, main landmark/focus target and footer.
- Added a locale-catalog convention for future translated UI copy.
- Added focused contract tests for locale configuration, template loading, language propagation and accessibility landmarks.

## Checks

- GitHub Actions run `33700974947` on implementation head `fee6e623aff1f90b6d600c50a923adcf8a5ae26e` — PASS.
- Existing dependency/command contract tests — PASS.
- `make test` including the new i18n/base-layout tests — PASS.
- `make e2e` — PASS.
- `make smoke` — PASS.

## Corrected during verification

- The first test revision called Django translation APIs before the app registry was initialized under direct `unittest`; the test now performs `django.setup()` before rendering translated templates.

## Deviations

- None. Tailwind build, HTMX and minimal Alpine.js remain active in P0 and are not included in this step.
