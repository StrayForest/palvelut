# P6-06 — Повторная legal/privacy/policy проверка beta-flow

Статус: завершено 2026-09-10.

Исходный пункт P6 Readiness:

> Re-review provider terms, privacy/data fields, moderation wording and controller surfaces against the actual beta flow; unresolved legal/policy uncertainty blocks launch.

## Что проверено и изменено

- Повторно сопоставлен фактический P6 self-service flow с публичными provider terms, privacy notice, moderation wording и controller surfaces.
- Подтверждён контроллер бесплатной beta-версии: Aleksei Lisitcin, физическое лицо; сервис Finrix Palvelut (`finrix.fi`), privacy contact `aleksei.lisitsin1@gmail.com`.
- Privacy notice теперь явно описывает фактические категории P6-данных: account/auth records, legal/display identity, provider type/Y-tunnus, ownership evidence, terms version/acceptance timestamp, professional-right и employer-authorization references, profile data, moderation/trust records, data-rights records, security/audit events и first-party analytics.
- Зафиксированы цели/основания, источники, критерии хранения, категории processors/recipients, международные передачи и data-rights route.
- Provider terms приведены к фактическому eligibility contract и выпущены как версия `2026-09-10`; backend staff approval принимает только текущую версию.
- Условия явно отделяют Finrix Palvelut от договора между клиентом и специалистом, фиксируют ownership/content review как отдельные стадии и ограничивают смысл verification label только проверенным фактом/источником/датой.
- Public content-report wording сделан нейтральным: report не означает автоматическое удаление, reporter получает private status code, есть предупреждение не отправлять лишние sensitive data и описан пропорциональный staff review.
- Создан `docs/10-beta-legal-data-register.md` с фактическим data inventory и границами повторного review.
- Добавлены Django regression tests для privacy/terms/report contract.

## Правовая опора review

Проверка выполнена по официальному GDPR text (в частности, transparency requirements Articles 13–14) и официальным материалам European Commission по Digital Services Act. Техническая документация не утверждает неподтверждённую юридическую классификацию Finrix Palvelut; вместо этого сохраняется консервативный notice/report/appeal process и требование повторного review при расширении роли сервиса.

Официальные источники:

- `https://eur-lex.europa.eu/eli/reg/2016/679/oj`
- `https://digital-strategy.ec.europa.eu/en/policies/digital-services-act`

## Acceptance evidence

Implementation exact head: `823493d25bad1e81bb85edecc699f3c6d9d446bb`.

- Compose stack run `34416251536` — PASS, включая lint/format, mypy, dependency/secret gates, migrations, provider security/integration, canonical non-browser tests, canonical browser gate, Playwright evidence upload и disposable smoke.
- P5 load acceptance run `34416251522` — PASS.
- Production image run `34416251525` — PASS.
- Playwright artifact: `playwright-evidence-34416251536-1`.

Вручную просмотрены новые retained screenshots на ширинах `360 / 390 / 768 / 1024 / 1440` для:

- `provider-terms`;
- `privacy-notice`;
- `content-report-policy`.

Первый visual review обнаружил реальный дефект legal/privacy typography: существующий `prose` не давал ожидаемой визуальной иерархии в текущей Tailwind-сборке и мобильные страницы выглядели как плотная стена текста. Добавлены явные heading/paragraph/link styles. Повторный artifact просмотрен после исправления: заметных clipping, horizontal overflow, нечитаемой иерархии или сломанных form controls не осталось.

## Граница закрытия

Этот шаг закрывает только первый P6 Readiness-пункт. Он не означает общий legal sign-off на будущие функции. Новые категории персональных данных, реклама/cross-site tracking, платежи, booking/chat, user accounts либо изменение роли каталога требуют нового legal/privacy review до включения.
