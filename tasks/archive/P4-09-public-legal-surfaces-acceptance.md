# P4-09 — Public legal/controller/contact surfaces acceptance

Completed the active P4 acceptance criterion: public legal, controller and contact surfaces are complete after owner review for the initial free beta.

## Verification

- Finrix Palvelut / `finrix.fi` identifies Aleksei Lisitcin as the private-individual operator and data controller.
- Privacy and accessibility contact use `aleksei.lisitsin1@gmail.com`.
- Privacy, provider terms, cookie policy and accessibility surfaces no longer contain owner-review draft placeholders.
- The beta posture is stated without inventing a company, toiminimi or Y-tunnus, and without claiming statutory accessibility scope beyond the product WCAG 2.2 AA target.
- Reviewed legal surfaces are publicly indexable rather than marked `noindex`.

## Evidence

- Implementation exact head: `4f27cfab3dafaaa53f815b6711edbf570e687c2e`.
- GitHub Actions `Compose stack` run `33973380318`: PASS on the exact implementation head, including lint/format, type check, dependency/secret checks, builds, migrations, provider security/integration, canonical non-browser/browser gates, Playwright evidence and disposable smoke.

## Deviations

None.
