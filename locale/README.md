# UI language contract

The product and staff UI are Russian-only for the MVP.

Do not add Finnish or English UI locales, locale switching, or FI/EN translation catalogs. `/palvelut/ru/` is the only supported public UI prefix. Django i18n remains enabled only so framework-provided messages can use the Russian locale.

Provider spoken languages are domain data, not UI locales, and may include Russian, Finnish, English, or other supported service languages.
