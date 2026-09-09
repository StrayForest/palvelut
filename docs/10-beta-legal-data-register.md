# Реестр legal/privacy для beta

Статус: повторная P6-проверка фактического beta-flow перед набором специалистов. Этот документ фиксирует продуктовый и технический контракт, а не заменяет индивидуальную юридическую консультацию.

## Контроллер и границы сервиса

- Сервис: Finrix Palvelut, `finrix.fi`.
- Оператор и контроллер бесплатной beta-версии: Aleksei Lisitcin, физическое лицо.
- Контакт по privacy/accessibility: `aleksei.lisitsin1@gmail.com`.
- Сервис является каталогом: пользователь связывается со специалистом напрямую, Finrix Palvelut не является стороной договора на услугу и не гарантирует качество специалиста.
- В публичных материалах не заявляется наличие компании, toiminimi или Y-tunnus у оператора.

## Фактические категории данных

| Данные | Цель | Основание продукта | Хранение/удаление | Получатель/процессор и export/delete route |
|---|---|---|---|---|
| Email аккаунта, password hash, session/auth security records | регистрация, вход, безопасность аккаунта | действия по запросу специалиста для предоставления beta-сервиса; legitimate interest для безопасности | пока нужен аккаунт; security records — пока нужны для расследования/защиты и применимых обязанностей | приложение/БД и техническая email-инфраструктура; access/export/delete через `/palvelut/account/data-rights/` или privacy contact |
| Legal name, display name, provider type, Y-tunnus | eligibility, ownership review, карточка | предоставление provider-сервиса и проверка допустимости публикации | пока существует provider relationship и далее только пока запись нужна для решений, споров или применимых обязанностей | приложение/БД; публичными становятся только поля, предназначенные для одобренного профиля; data-rights route как выше |
| Ownership evidence kind/reference, claimant id, submitted/reviewed timestamps | доказательство контроля карточки | предоставление provider-сервиса; legitimate interest в предотвращении impersonation/fraud и документировании решения | приватно, пока запись нужна для доказательства решения, споров, abuse prevention или применимых обязанностей | приложение/БД, staff review; не публикуется посетителям; data-rights route как выше |
| Provider terms version и acceptance timestamp | доказательство принятой версии условий | предоставление provider-сервиса и документирование договорного состояния | вместе с claim/audit history, пока это необходимо для provider relationship и связанных споров/обязанностей | приложение/БД и staff review; data-rights route как выше |
| Professional-right reference и employer-authorization reference для employed regulated professional | eligibility и проверка права быть опубликованным | предоставление provider-сервиса; legitimate interest в точности и безопасности каталога | приватно, пока необходимо для eligibility/verification history, споров и применимых обязанностей | приложение/БД и staff review; публично может отображаться только отдельно проверенный факт/источник, а не автоматически submitted evidence; data-rights route как выше |
| Services, areas, languages, description, prices, photos, contacts | публичная карточка и поиск | предоставление provider-сервиса по запросу специалиста | пока карточка активна; live/pending revision history — пока нужна для модерации и аудита | приложение/БД/object storage/CDN по deployment inventory; публикация только после review; data-rights route как выше |
| Verification sources/facts/check dates | точные trust labels | legitimate interest в точности каталога и предотвращении misleading claims | пока факт используется публично и далее пока history нужен для аудита/споров | staff/application DB; публично показывается только конкретный одобренный факт и дата проверки |
| Content report category/details/status token hash; provider appeal/reply; staff notes/decisions | notice, moderation, correction, appeal | legitimate interest в безопасном и точном каталоге; применимая legal obligation, если она возникает | пока нужно обработать case, документировать решение, споры, abuse и применимые обязанности | приложение/БД и staff; reporter получает только private status token; data-rights/privacy contact для запросов |
| Data-subject request и event history | access/export/delete workflow | выполнение GDPR/data-rights запроса и документирование обработки | пока нужно выполнить и доказать обработку запроса и применимые обязанности | приложение/БД и MFA-protected staff workflow |
| Request ID, audit/security events | диагностика, расследование abuse/security | legitimate interest в безопасности и надёжности | только пока нужны для этих целей и применимых обязанностей | приложение/logging infrastructure; не использовать для product profiling |
| First-party analytics events: session id, normalized search dimensions, FI country signal, event/schema/bot rule versions | beta funnel, zero-result и release decision | legitimate interest в измерении и улучшении минимального каталога | raw events удаляются после 90 дней; daily aggregates не содержат visitor identity | analytics DB/operations stack; не собирать account id, IP, precise location, message body или cross-site identifier |

`Основание продукта` выше описывает принятый технический контракт. Если конкретная обработка требует иного юридического основания по закону, публичный notice и реализация должны быть обновлены до её включения.

## Источники и прозрачность

- Account/onboarding/profile данные обычно поступают от самого специалиста.
- Для verification допускаются идентифицированные официальные публичные источники, включая финские business/professional registers.
- Imported provider остаётся непубличным до доказательства контроля и staff approval.
- Privacy notice сообщает категории данных, цели/основания, источники, критерии хранения, категории processors/recipients, data-rights route и правило для международной передачи.
- Если production processor обрабатывает персональные данные вне EU/EEA, он не включается без применимого GDPR transfer mechanism/safeguards; конкретный processor inventory является deployment/operations inventory и должен соответствовать публичному notice.

## Provider terms review

Текущая версия условий: `2026-09-10`.

Она явно фиксирует:

1. beta бесплатна, каталог не является работодателем/агентом/стороной договора пользователя со специалистом;
2. business/self-employed требует активный Finnish Y-tunnus и совпадающую legal identity;
3. employed regulated professional требует review identity, applicable professional right и employer authorization;
4. claimant обязан доказать контроль независимо от одного владения email;
5. ownership approval не публикует карточку — content review отдельный;
6. verification label подтверждает только явно указанный факт, источник и дату;
7. moderation может исправлять, отклонять, unpublish/suspend/archive контент, а provider имеет provider-visible notice/appeal path;
8. ownership/eligibility evidence приватно и само по себе не публикуется;
9. материальное изменение условий создаёт новую version; новый ownership approval требует принятия текущей версии.

## Moderation wording review

Публичный report-flow описывается нейтрально и не обещает автоматическое удаление. Reporter может указать suspected illegal content, impersonation, inaccurate/outdated information или другой policy concern без аккаунта, получает приватный status code и предупреждение не включать лишние sensitive data. Staff принимает пропорциональное решение; provider-visible notices и appeal остаются частью существующего workflow.

Для beta применяется консервативный DSA-aware moderation process без утверждения в продукте о конкретной юридической классификации сервиса. Текущий продукт уже имеет report, status, notice, decision history и provider appeal. Если перед публичным запуском бизнес-модель или функциональность меняется в сторону marketplace/hosting обязанностей, применимость и дополнительные DSA-обязанности пересматриваются до запуска.

## Основания review

- GDPR Article 13 требует при сборе данных сообщать identity/contact controller, purposes/legal basis, recipients/categories, применимые international transfers, retention period/criteria и data-subject rights.
- GDPR Article 14 добавляет source transparency, когда данные получены не от самого data subject.
- Европейская комиссия указывает, что DSA охватывает online intermediaries/platforms пропорционально роли и размеру; поэтому beta сохраняет notice-and-action/appeal controls и не полагается на предположение, что каталог автоматически находится вне DSA.

Официальные ссылки: `https://eur-lex.europa.eu/eli/reg/2016/679/oj` и `https://digital-strategy.ec.europa.eu/en/policies/digital-services-act`.

## P6 launch decision

По состоянию на эту проверку фактические P6 onboarding fields, provider terms, privacy/controller surface и moderation wording согласованы с текущим узким beta-flow. Новые категории персональных данных, реклама/cross-site tracking, платежи, booking/chat, user accounts или изменение роли каталога требуют повторной legal/privacy review до включения.
