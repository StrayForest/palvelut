# P6 — Helsinki beta

Depends: P5. Read: `docs/01-product.md`, `docs/03-experience.md`, `docs/04-design.md`, `docs/06-quality.md`.

## Readiness

- Retain and manually review full-page screenshots for provider acquisition/onboarding at 360, 390, 768, 1024 and 1440 px: public CTA, `for-professionals`, register/login, new-provider bootstrap/claim state, workspace, edit and preview. Check hierarchy, design tokens, focus/error states, text expansion and horizontal overflow.
- Run a fresh-account beta rehearsal: register → verify email → start/claim provider → staff approve ownership → complete profile → preview → submit → staff approve content → discover public profile → use tracked contact. The primary rehearsal account must not be granted membership by fixture/database setup.
- Re-review provider terms, privacy/data fields, moderation wording and controller surfaces against the actual beta flow; unresolved legal/policy uncertainty blocks launch.
- Connect Search Console/Bing, production monitoring and the funnel/dashboard used for the beta decision; freeze metric, schema and bot-rule versions and reconcile raw events to aggregates before launch.

Do not start provider recruitment for the launch-density target until all Readiness items above are complete and archived.

## Operate

- Manually recruit/onboard 50 providers and meet every pre-launch density gate.
- Review all public content and verification wording; suppress thin pages.
- Launch through Finrix with one clear search promise and provider CTA.
- Run 30 days; interview providers/users and record aggregate outcomes.
- Reconcile raw events to aggregates and sample at least 20 eligible users using the frozen definitions.

## Decide

Compare results with all beta gates in `docs/01-product.md`.

Record each numerator, denominator, exclusion rule, provider confirmation sample and data-quality result. If any gate cannot be computed from its written definition, the decision is `ITERATE`, not `GO`.

- **GO:** improve density/trust/SEO; then evaluate P7.
- **ITERATE:** one bounded 30-day experiment tied to a failed metric.
- **STOP:** archive acquisition work and keep/remove the directory based on maintenance cost.

Do not reinterpret pageviews or contact clicks as completed jobs.
