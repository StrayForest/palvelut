# P6-04 — Полный provider visual evidence set

## Что закрыто

Закрыт четвёртый readiness-шаг P6: сохранён и вручную проверен полный набор full-page Playwright screenshots для provider acquisition/onboarding на ширинах 360, 390, 768, 1024 и 1440 px.

## Контракт evidence

На каждой предусмотренной ширине сохраняются и проходят автоматическую проверку отсутствия горизонтального overflow следующие состояния:

- публичный provider CTA;
- `for-professionals` на EN, FI и RU для проверки text expansion;
- registration;
- registration с keyboard focus;
- login;
- login с validation error;
- empty provider workspace;
- new-provider bootstrap/start;
- new-provider start с eligibility validation errors и keyboard focus;
- ownership pending;
- workspace edit;
- workspace preview.

Итого retained evidence set содержит 70 PNG: 14 состояний × 5 ширин.

## Что исправлено при ручном review

Первоначальный evidence set не подтверждал заявленный field-error state формы `provider-start`: в artifact были login errors, но не было validation errors для нового provider. Перед закрытием шага добавлен реальный invalid-flow для `Employed regulated professional`: форма показывает обязательные ошибки `Professional-right reference` и `Employer authorization`, фокус устанавливается на первое проблемное поле, после чего состояние сохраняется на всех пяти ширинах.

Preview profile также приведён к общей визуальной системе provider workspace: responsive-карточка, service/price/contact/business identity sections, локализуемые подписи и явные `Submit for review` / `Back to edit` действия.

## Ручная визуальная проверка

Полный evidence set просмотрен вручную. Проверены:

- визуальная иерархия и design tokens;
- mobile/desktop навигация;
- читаемость длинных FI/RU строк;
- focus ring и error states;
- формы bootstrap/edit;
- preview composition;
- отсутствие clipping и горизонтального overflow.

Блокирующих визуальных дефектов после добавления недостающего error-state evidence не обнаружено.

## Проверки implementation head

Implementation head: `cbb4ac58aad4eedf78d490aadf5597b89c155ebb`.

- `Compose stack` run `34407428800` — PASS, включая lint/format, mypy, dependency audit, secret scan, reproducible build, migrations, provider security/integration, полный non-browser gate, Playwright browser gate, evidence upload и disposable smoke.
- `Production image` run `34407428772` — PASS, включая SBOM и scan fixed critical vulnerabilities.
- Playwright artifact exact head: `playwright-evidence-34407428800-1`.

## Что остаётся активным

Этот архив закрывает только visual evidence readiness. Следующий P6 readiness-пункт — fresh-account beta rehearsal полного end-to-end пути — остаётся в `tasks/P6-beta.md` и в рамках этого шага не начинается.
