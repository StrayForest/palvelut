# P6-01 — Самостоятельный старт специалиста

Закрыт первый пункт Readiness этапа P6: новый подтверждённый пользователь может начать путь специалиста без заранее созданных staff-записей `Provider`/`ProviderMembership`.

## Что реализовано

- публичный CTA для специалистов и отдельная страница `for-professionals`;
- регистрация/вход и переход в кабинет специалиста;
- создание приватной карточки специалиста новым подтверждённым аккаунтом;
- подача независимого подтверждения контроля/владения;
- состояния ожидания/отклонения ownership review;
- создание membership только после существующего staff approval;
- self-created профиль остаётся непубличным до ownership approval и последующей модерации контента;
- Django regression coverage и Playwright fresh-account flow.

## Проверка

Implementation head: `93b5fc72b980c6377acdfac64a1cf1a6696bb624`.

Exact-head gates:

- Compose stack — PASS;
- Production image — PASS;
- P5 load acceptance — PASS;
- lint/format, mypy, dependency audit, secret scan — PASS;
- migrations, provider security/integration, полный non-browser gate — PASS;
- canonical browser gate и disposable smoke gate — PASS.

Playwright сохранил P6 evidence на ширинах 360, 390, 768, 1024 и 1440 px для публичного CTA, `for-professionals`, register/login, provider bootstrap, pending ownership и workspace. Скриншоты просмотрены вручную после PASS; заметных горизонтальных переполнений, сломанных состояний или блокирующих визуальных дефектов не обнаружено.

## Что не закрывает этот шаг

Остаются активными: принятие provider terms и legal/identity contract, полный UX/localization polish кабинета, отдельный visual acceptance edit/preview, полная beta rehearsal до публичного профиля и tracked contact, legal/data re-review и production beta instrumentation.
