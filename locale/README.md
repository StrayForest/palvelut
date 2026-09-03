# Locale catalogs

Supported UI locales are `ru`, `fi`, and `en`.

Django message catalogs live under `locale/<language>/LC_MESSAGES/` as copy is added. English source strings remain the technical source language; user-facing strings must use Django i18n tags/functions rather than hard-coded locale branching.
