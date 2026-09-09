# P6-03 — Provider surfaces: дизайн, локализация и status/next-action contract

## Что закрыто

Закрыт третий readiness-шаг P6: provider auth/onboarding/workspace приведены к design + localization contract с единообразной навигацией, явными состояниями `Current status` / `Next action` и cache-safe поведением приватных поверхностей.

## Контракт

- Provider login, registration, `for-professionals`, self-start и workspace используют общий визуальный язык и компоненты базового layout.
- Пользовательские строки provider auth/onboarding/workspace вынесены в локализуемые Django-строки; формы используют локализуемые labels/help/error messages.
- Workspace сначала показывает фактический статус профиля и конкретное следующее действие, а не универсальную кнопку редактирования.
- Для незаполненного профиля CTA ведёт к продолжению заполнения; для ownership review и pending content review интерфейс явно сообщает, что требуется ожидание, и не предлагает действие, обходящее review.
- Навигация к `For professionals`, provider workspace и sign-in остаётся видимой и согласованной на публичных и приватных поверхностях.
- Приватные account/workspace ответы сохраняют cache-safe semantics и не превращаются в публично кэшируемые страницы.
- P3 browser regression обновлён под state-driven workspace: после submit профиль имеет `Pending / Revision Pending`, поэтому accessibility smoke проверяет реальное pending-состояние, keyboard focus и axe без повторного входа в редактор.

## UI и ручная проверка

Playwright evidence exact implementation head вручную просмотрен для ширин 360, 390, 768, 1024 и 1440 px на поверхностях:

- публичный provider CTA;
- `for-professionals`;
- registration;
- login;
- new-provider start;
- empty workspace;
- ownership pending.

Проверены визуальная иерархия, поля форм, CTA, status/next-action карточки, навигация и адаптивность. Заметных горизонтальных overflow, clipping, невидимых полей или сломанной иерархии не обнаружено.

## Проверки implementation head

Implementation head: `0bd44a545c3a177e132f046d783e3a27c37b48ef`.

- `Compose stack` run `34402287650` — PASS, включая lint/format, mypy, dependency audit, secret scan, reproducible build, migrations, provider security/integration, полный non-browser gate, Playwright browser gate, evidence upload и disposable smoke.
- `Production image` run `34402287565` — PASS.
- `P5 load acceptance` run `34402287744` — PASS.
- Playwright artifact exact head: `playwright-evidence-34402287650-1`.

## Что остаётся активным

Следующие readiness-шаги остаются только в `tasks/P6-beta.md`; этот архив не закрывает и не начинает их. Отдельный следующий пункт про полный набор и ручной review acquisition/onboarding screenshots остаётся активным, даже несмотря на то, что этот шаг уже использовал screenshots как acceptance evidence.
