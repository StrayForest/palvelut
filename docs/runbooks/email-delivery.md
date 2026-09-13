# Доставка системных писем

## Назначение

Этот runbook относится к письмам подтверждения регистрации и сброса пароля Finrix Palvelut.

Локальная среда использует Mailpit. Staging и production обязаны использовать внешний SMTP-сервис с аутентификацией и защищённым транспортом. Mailpit, localhost и адрес отправителя в домене `.invalid` в production запрещены конфигурацией приложения.

## Обязательные production-переменные

```text
EMAIL_HOST=<smtp-host>
EMAIL_PORT=587
EMAIL_HOST_USER=<smtp-user>
EMAIL_HOST_PASSWORD=<secret>
EMAIL_USE_TLS=1
EMAIL_USE_SSL=0
EMAIL_TIMEOUT=10
DEFAULT_FROM_EMAIL=<подтверждённый адрес отправителя>
```

Для SMTP через порт 465 используется `EMAIL_USE_SSL=1` и `EMAIL_USE_TLS=0`. Одновременное включение TLS и SSL запрещено.

Секрет `EMAIL_HOST_PASSWORD` хранится только во внешнем production env-файле на сервере. Его нельзя помещать в Git, CI-логи или документацию.

## Пример для Resend SMTP

Если используется Resend:

```text
EMAIL_HOST=smtp.resend.com
EMAIL_PORT=587
EMAIL_HOST_USER=resend
EMAIL_HOST_PASSWORD=<Resend API key>
EMAIL_USE_TLS=1
EMAIL_USE_SSL=0
EMAIL_TIMEOUT=10
DEFAULT_FROM_EMAIL=Finrix Palvelut <noreply@ваш-подтверждённый-домен>
```

Домен отправителя должен быть подтверждён у провайдера до production-теста.

## Проверка после изменения конфигурации

1. Перезапустить web-контейнеры с обновлённым env-файлом.
2. Выполнить production `manage.py check --deploy`.
3. Зарегистрировать тестового специалиста на реальный контролируемый почтовый адрес.
4. Убедиться, что письмо пришло во внешний почтовый ящик, а не только принято SMTP-сервером.
5. Проверить, что ссылка ведёт на `https://finrix.fi/palvelut/account/verify/...` и после перехода аккаунт становится активным.
6. Проверить письмо сброса пароля тем же способом.
7. Проверить spam/junk и журнал провайдера, если письмо не появилось в течение нескольких минут.

## Если письмо не приходит

- `connection refused`, DNS/TLS error: проверить `EMAIL_HOST`, порт, исходящий firewall и TLS/SSL режим;
- `535`/authentication failed: заменить SMTP credential;
- SMTP принял письмо, но получатель его не видит: проверить provider delivery log, bounce/suppression, SPF/DKIM/DMARC и spam;
- письмо ушло в Mailpit: production запущен с локальной конфигурацией — исправить env и перезапустить контейнеры;
- неверный sender/domain: использовать только подтверждённый `DEFAULT_FROM_EMAIL`.

Не считать HTTP `201` после регистрации доказательством доставки. Acceptance для production — письмо реально получено внешним почтовым ящиком и ссылка успешно активирует аккаунт.
