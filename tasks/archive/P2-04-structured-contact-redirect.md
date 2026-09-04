# P2-04 — Structured contact redirect

Status: complete.

## Scope

Complete the next P2 build step only: structured contact redirect with server-side destination resolution and a minimal analytics event.

## Completed

- Added an opaque `/palvelut/{locale}/go/{provider}/{channel}/` route that resolves only stored `ContactChannel` data for published providers and public channels.
- Request-supplied destination parameters are ignored; invalid or unsupported stored destinations fail closed.
- Added structured handling for phone, email, website, booking, Telegram and WhatsApp destinations without exposing stored contact values in the route.
- Added a minimal `AnalyticsEvent` containing only event kind, provider, channel and timestamp; destination/contact values are not persisted in analytics.
- Contact redirects return `302` with `private, no-store`, and provider profile contact actions now point through the internal route.
- Added regression coverage for stored-target resolution, malicious destination-query input, private channels, suspended providers and invalid stored targets.

## Verification

Exact-head Compose CI `33904143701` passed all 24 steps for `9aaeca833b7caafeac536aa0301538910faf1259`, including lint/format, mypy, dependency audit, secret scan, frontend/application builds, migrations, non-browser tests, browser gate, retained Playwright evidence and disposable smoke.
