# Доставка системных писем

## Текущий beta-режим

До подключения собственного домена production может работать полностью без исходящей почты:

```text
EMAIL_DELIVERY_ENABLED=0
ACCOUNT_EMAIL_VERIFICATION_REQUIRED=0
```

В этом режиме:

- регистрация не создаёт письмо подтверждения;
- новый аккаунт сразу становится активным;
- verification-token не создаётся;
- Django использует dummy email backend, поэтому наружу ничего не отправляется;
- ранее созданный, но неактивированный аккаунт можно повторно зарегистрировать тем же email — он будет активирован без смены старого пароля.

Это временный beta-режим. Он сознательно убирает подтверждение владения email, поэтому его нужно отключить перед публичным запуском, когда появится рабочий домен отправителя.

## Включение email позже

После подключения домена установить:

```text
EMAIL_DELIVERY_ENABLED=1
ACCOUNT_EMAIL_VERIFICATION_REQUIRED=1
EMAIL_HOST=<smtp-host>
EMAIL_PORT=587
EMAIL_HOST_USER=<smtp-user>
EMAIL_HOST_PASSWORD=<secret>
EMAIL_USE_TLS=1
EMAIL_USE_SSL=0
EMAIL_TIMEOUT=10
DEFAULT_FROM_EMAIL=<подтверждённый адрес отправителя>
```

Когда `EMAIL_DELIVERY_ENABLED=1`, staging/production снова требуют внешний SMTP с аутентификацией, защищённым транспортом и доставляемым sender. Mailpit, localhost и sender в `.invalid` будут отклонены fail-fast проверкой.

Для SMTP через порт 465 используется `EMAIL_USE_SSL=1` и `EMAIL_USE_TLS=0`. Одновременное включение TLS и SSL запрещено.

Секрет `EMAIL_HOST_PASSWORD` хранится только во внешнем production env-файле на сервере. Его нельзя помещать в Git, CI-логи или документацию.

## Пример для Resend SMTP

```text
EMAIL_DELIVERY_ENABLED=1
ACCOUNT_EMAIL_VERIFICATION_REQUIRED=1
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

## Проверка после включения email

1. Перезапустить web-контейнеры с обновлённым env-файлом.
2. Выполнить production `manage.py check --deploy`.
3. Зарегистрировать тестового специалиста на реальный контролируемый почтовый адрес.
4. Убедиться, что письмо пришло во внешний почтовый ящик.
5. Проверить, что ссылка ведёт на `/palvelut/account/verify/...` и после перехода аккаунт становится активным.
6. Проверить письмо сброса пароля тем же способом.
7. Проверить spam/junk и журнал провайдера, если письмо не появилось.
