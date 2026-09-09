# P6-05 — Fresh-account beta rehearsal

Статус: завершено.

## Цель

Подтвердить единым acceptance-сценарием реальный путь нового специалиста от отсутствующего аккаунта до публичной карточки и отслеживаемого контакта без предварительного создания `ProviderMembership` через fixture или прямую подготовку базы.

## Что проверено

- новый provider-account отсутствует до начала сценария;
- регистрация создаёт неактивный аккаунт и отправляет письмо подтверждения;
- переход по verification URL активирует аккаунт;
- успешный вход ведёт в provider workspace;
- до staff approval у основного rehearsal-account отсутствует `ProviderMembership`;
- специалист самостоятельно создаёт provider и отправляет ownership claim с обязательными provider terms и eligibility evidence;
- staff approval ownership создаёт активное owner-membership;
- владелец заполняет профиль, сервис, географию, язык и публичный контакт;
- preview показывает подготовленный контент;
- владелец отправляет revision на проверку;
- staff approval content переводит provider в `published`;
- approval атомарно создаёт стабильный public slug и `ProviderReadDocument`, поэтому состояние `published-but-invisible` невозможно;
- опубликованный provider находится через public search и открывается по public profile URL;
- tracked contact возвращает ожидаемый `mailto:` redirect и создаёт `contact_click` analytics event.

## Найденный и исправленный разрыв

До этого шага `approve_revision()` менял lifecycle на `published`, но сам по себе не создавал public slug и discovery read model. Provider мог считаться опубликованным в write-модели и при этом отсутствовать в публичном discovery/profile path.

Publication path исправлен: создание slug и перестроение public read document выполняются в той же транзакции, что и staff content approval.

## Acceptance evidence

Exact-head CI после реализации:

- canonical non-browser gate — PASS, включая `FreshAccountBetaRehearsalTests`;
- P3 provider security/integration gate — PASS;
- canonical browser gate — PASS;
- Playwright evidence upload — PASS;
- disposable smoke — PASS;
- P5 load acceptance — PASS;
- Production image — PASS.

UI/design в этом шаге не изменялись, поэтому новых визуальных состояний для отдельного screenshot-review не создавалось; существующий browser gate и retained Playwright evidence прошли без регрессий.
