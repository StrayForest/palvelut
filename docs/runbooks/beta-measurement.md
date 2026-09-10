# Измерение Helsinki beta

Этот runbook фиксирует измерительный контракт P6. Версии нельзя менять во время 30-дневного beta-окна без нового bounded experiment и явной записи причины.

## Замороженные версии

- schema: `p6-beta-schema-v1`;
- metrics: `p6-beta-metrics-v1`;
- bot rules: `p6-beta-bots-v1`.

Raw-событие хранит только случайный first-party `session_id`, тип события, `FI`/другой двухбуквенный country code, provider/channel там, где это необходимо для contact conversion, результативность поиска и три версии выше. IP, User-Agent, account/user id, fingerprint и текст поискового запроса в beta event не сохраняются.

Сессия живёт 30 минут без активности. Cookie `palvelut_beta_session` обновляется только через отдельный `private, no-store` collector/contact response и не делает публичный HTML некэшируемым.

## Что считается

30-дневный reconciled snapshot считает:

- Finland-based discovery sessions — уникальные `session_id` с public home/results/profile activity и `country_code=FI`;
- search sessions — уникальные с хотя бы одним нормализованным поиском/фильтром;
- search → contact conversion — search sessions, где после первого search произошёл tracked contact click;
- zero-result ratio — доля search events без результатов.

Contact click дедуплицируется по `(session, provider, channel)` в пределах 30 минут. Просмотры/поиски verified bots и UA, совпавшие с замороженным bot list, не записываются.

## Raw → aggregate reconciliation

Перед стартом beta и затем ежедневно выполнить/проверить:

```bash
python manage.py reconcile_beta_funnel
```

Команда создаёт immutable `BetaDecisionSnapshot`, печатает JSON с numerator/denominator, версиями и SHA-256 checksum исходного raw-набора и обновляет Prometheus gauges. Celery Beat выполняет ту же сверку ежедневно в 03:15 Europe/Helsinki.

Перед решением GO/ITERATE/STOP сравнить последний snapshot с raw events той же версии. Если версии отличаются, checksum не воспроизводится или метрика не вычисляется по определению из `docs/01-product.md`, решение автоматически `ITERATE`.

## Production monitoring/dashboard

Prometheus получает beta gauges через защищённый `/palvelut/metrics`; Grafana JSON находится в `infra/observability/dashboard.json`. Для beta обязательны панели:

- FI discovery sessions — 30d;
- search sessions — 30d;
- search → contact conversion;
- zero-result ratio;
- reconciled raw event count.

Collector `/palvelut/analytics/collect/` обязан обходить Cloudflare cache. Edge передаёт `CF-IPCountry` и динамический `X-Palvelut-Verified-Bot` из `cf.client.bot`. Если production collector видит неизвестную страну, такой event не входит в Finland gate.

## Google Search Console и Bing Webmaster Tools

Верификационные значения хранятся только в production secrets:

```text
GOOGLE_SITE_VERIFICATION=<Google meta verification value>
BING_SITE_VERIFICATION=<Bing msvalidate.01 value>
```

После задания secrets и deploy:

1. открыть публичную `/palvelut/en/` и убедиться, что присутствуют `google-site-verification` и `msvalidate.01` с ожидаемыми значениями;
2. завершить ownership verification в Google Search Console и Bing Webmaster Tools для `https://finrix.fi/`;
3. в обеих консолях отправить `https://finrix.fi/palvelut/sitemap.xml`;
4. проверить, что `/palvelut/*/search/` не индексируется, а публичные canonical/profile/landing URL читаются из sitemap;
5. сохранить в release evidence дату подтверждения ownership и дату успешного чтения sitemap — без самих verification secrets.

Значения verification token нельзя коммитить, логировать или помещать в screenshot artifacts.

## Перед включением provider recruitment

- Search Console ownership подтверждён и sitemap прочитан;
- Bing ownership подтверждён и sitemap прочитан;
- production `/metrics` реально scrape-ится;
- collector bypass cache применён в Cloudflare;
- verified-bot header transform применён;
- `reconcile_beta_funnel` создал snapshot без ошибок;
- версии snapshot точно `p6-beta-schema-v1` / `p6-beta-metrics-v1` / `p6-beta-bots-v1`.

Если любой пункт не подтверждён на production, Readiness не считается завершённым и recruitment нельзя начинать.
