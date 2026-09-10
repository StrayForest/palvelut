# P6-07 — Готовность измерений Helsinki beta

Статус: завершено 2026-09-10.

Исходный пункт P6 Readiness:

> Connect Search Console/Bing, production monitoring and the funnel/dashboard used for the beta decision; freeze metric, schema and bot-rule versions and reconcile raw events to aggregates before launch.

## Что реализовано

- Зафиксирован privacy-safe измерительный контракт Helsinki beta: raw events не сохраняют IP, User-Agent, account/user id, fingerprint или текст поискового запроса.
- Сессии beta определяются first-party случайным `session_id` с 30-минутным inactivity window.
- Заморожены версии `p6-beta-schema-v1`, `p6-beta-metrics-v1` и `p6-beta-bots-v1`; событие и reconciled snapshot несут эти версии явно.
- Добавлена raw-event → aggregate reconciliation за 30 дней с immutable `BetaDecisionSnapshot`, numerator/denominator и SHA-256 checksum исходного набора событий.
- Добавлены beta decision gauges в Prometheus/Grafana для Finland discovery sessions, search sessions, search→contact conversion, zero-result ratio и reconciled raw event count.
- Cloudflare contract исключает `/palvelut/analytics/collect/` из cache и передаёт verified-bot edge signal; verified bots исключаются из beta measurement.
- Добавлены production-настройки мета-верификации Google Search Console и Bing Webmaster Tools без хранения verification token в репозитории.
- Создан русскоязычный runbook `docs/11-beta-measurement-runbook.md` с frozen definitions, reconciliation procedure, production dashboard/monitoring contract и checklist для Search Console/Bing.
- Добавлены migration и acceptance/regression tests для collection, privacy boundary, search-engine verification, reconciliation и measurement versions.

## Найденный CI-регресс

Первый exact-head прогон выявил рассинхрон старого `.env.example` contract test: новые безопасные пустые поля `GOOGLE_SITE_VERIFICATION` и `BING_SITE_VERIFICATION` отсутствовали в `expected_keys`. Тест обновлён так, чтобы оба поля были частью разрешённого runtime contract и одновременно обязательно оставались пустыми в example-файле. Проверки реальных credential placeholders не ослаблялись.

## Acceptance evidence

Implementation exact head после исправления contract test: `5021765ecb7cadaa31bb60141873a3d6c7b0f9fe`.

- Compose stack run `34421466157` — PASS, включая bootstrap, lint/format, mypy, dependency audit, secret scan, reproducible build, migrations, provider security/integration, canonical non-browser tests, canonical browser gate, Playwright evidence upload и disposable smoke.
- P5 load acceptance run `34421466155` — PASS.
- Production image run `34421466175` — PASS.

Шаг не меняет видимые пользовательские или дизайн-поверхности: Search Console/Bing verification добавляется только как невидимые `<meta>`-значения, а остальные изменения относятся к analytics/monitoring/edge contracts. Поэтому отдельный новый visual screenshot-state не требовался; canonical browser gate и retained Playwright evidence прошли.

## Граница закрытия

Этот шаг закрывает P6 Readiness на уровне кода, конфигурационных контрактов, frozen measurement definitions и production runbook. Фактические production secrets/ownership verification в Google Search Console и Bing, применение Cloudflare rule/header transform и реальный scrape `/metrics` должны подтверждаться при production rollout по runbook; verification tokens не коммитятся и не входят в artifacts.
