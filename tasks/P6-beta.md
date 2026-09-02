# P6 — Helsinki beta

Depends: P5. Read: `docs/01-product.md`, `docs/02-research.md`.

## Operate

- Manually recruit/onboard 50 providers and meet every pre-launch density gate.
- Review all public content and verification wording; suppress thin pages.
- Connect Search Console/Bing, production monitoring and funnel dashboard.
- Launch through Finrix with one clear search promise and provider CTA.
- Run 30 days; interview providers/users and record aggregate outcomes.
- Freeze metric/schema/bot-rule versions before launch; reconcile raw events to aggregates and sample at least 20 eligible users.

## Decide

Compare results with all beta gates in `docs/01-product.md`.

Record each numerator, denominator, exclusion rule, provider confirmation sample and data-quality result. If any gate cannot be computed from its written definition, the decision is `ITERATE`, not `GO`.

- **GO:** improve density/trust/SEO; then evaluate P7.
- **ITERATE:** one bounded 30-day experiment tied to a failed metric.
- **STOP:** archive acquisition work and keep/remove the directory based on maintenance cost.

Do not reinterpret pageviews or contact clicks as completed jobs.
