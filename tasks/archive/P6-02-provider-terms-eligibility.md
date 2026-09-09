# P6-02 — Условия специалиста и eligibility contract

## Что закрыто

Закрыт второй readiness-шаг P6: до ownership review специалист обязан явно принять текущую версию условий, а собранные legal/identity данные теперь соответствуют eligibility contract.

## Контракт

- Для `business` / self-employed provider обязателен Finnish Y-tunnus; без него ownership claim не отправляется.
- Для `individual` (employed regulated professional) обязательны две независимые ссылки/свидетельства: official professional-right reference и employer authorization to list services.
- Принятие provider terms обязательно как в новом self-start flow, так и при claim существующей карточки.
- Claim сохраняет серверную версию provider terms и timestamp принятия вместе с ownership/eligibility evidence.
- Staff approval повторно проверяет допустимый ownership evidence, текущую версию условий и eligibility evidence на сервисном уровне; прямой POST или внутренний вызов сервиса не обходят требования.
- Staff может отклонить старый/неполный pending claim, но не может одобрить его без текущего контракта.
- До approval активный `ProviderMembership` не создаётся и карточка не публикуется.

## UI и ручная проверка

Playwright сохраняет full-page evidence для provider acquisition/onboarding на ширинах 360, 390, 768, 1024 и 1440 px. При ручном просмотре первого набора обнаружено, что два поля eligibility для employed professional рендерились большими textarea и чрезмерно растягивали business-flow на мобильных ширинах. Поля переведены в компактные reference inputs без изменения валидации.

Повторные PNG на всех пяти ширинах вручную просмотрены: горизонтального overflow и блокирующих визуальных дефектов после исправления не обнаружено.

## Проверки implementation head

Implementation head: `9dda11b1d52b3f21c4ae1c748a5d2075ef9f5cd3`.

- `Compose stack` run `34394020469` — PASS, включая lint/format, mypy, dependency audit, secret scan, reproducible build, migrations, provider security/integration, полный non-browser gate, Playwright browser gate, evidence upload и disposable smoke.
- `Production image` run `34394020417` — PASS.
- `P5 load acceptance` run `34394020437` — PASS.
- Playwright artifact для этого exact head: `playwright-evidence-34394020469-1`.

## Что остаётся активным

Следующие readiness-шаги остаются только в `tasks/P6-beta.md`; этот архив не закрывает и не начинает их.
