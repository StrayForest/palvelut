# Synthetic monitoring

Production synthetic checks run from GitHub Actions every five minutes and can also be started manually. They exercise the public path through the external HTTPS origin rather than the host-local upstream.

## Required configuration

Repository secrets:

- `SYNTHETIC_BASE_URL` — production public base ending at `/palvelut`.
- `SYNTHETIC_PROFILE_SLUG` — slug of a dedicated published synthetic provider.
- `SYNTHETIC_PROVIDER_ID` — UUID of that same provider.
- `SYNTHETIC_MONITOR_TOKEN` — random secret shared with the production application environment.

Optional repository variables:

- `SYNTHETIC_LOCALE` — defaults to `en`.
- `SYNTHETIC_CONTACT_CHANNEL` — defaults to `website`; the synthetic provider must expose that public channel.

The application production env must contain the same `SYNTHETIC_MONITOR_TOKEN`. Rotate it like any operational secret and update the application plus GitHub secret together.

## Probes

`infra/scripts/synthetic-monitor.sh` fails fast if any of these checks fail:

1. home returns a successful HTML document;
2. search returns a successful HTML document;
3. the configured published provider profile returns a successful HTML document;
4. contact redirect returns `302` with a supported destination scheme.

Each request has bounded connect/total timeouts, requires HTTPS/TLS 1.2+, uses a dedicated user agent and sends the authenticated synthetic header. The application excludes authenticated synthetic requests from provider impression/profile/contact analytics so monitoring cannot contaminate the business funnel.

## Failure handling

Treat a scheduled workflow failure as an availability signal. Check, in order: DNS/Cloudflare, TLS, Nginx/upstream health, `/palvelut/health/ready`, application logs/Sentry, database/Valkey, and whether the configured synthetic provider is still published with the expected contact channel. Do not replace the synthetic provider with a real provider account or personal contact data.

After recovery, run the workflow manually once and confirm all four probes pass. Repeated failures should be correlated with the observability dashboard and incident runbook rather than suppressed by increasing timeouts.
