from pathlib import Path
from unittest import TestCase

import django
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import translation


django.setup()


class I18nBaseLayoutContractTests(TestCase):
    def test_supported_languages_are_ru_fi_en(self):
        self.assertEqual([code for code, _ in settings.LANGUAGES], ["ru", "fi", "en"])
        self.assertIn(settings.BASE_DIR / "locale", settings.LOCALE_PATHS)
        self.assertIn("django.middleware.locale.LocaleMiddleware", settings.MIDDLEWARE)

    def test_base_template_has_accessibility_landmarks_and_language(self):
        with translation.override("fi"):
            html = render_to_string("base.html")

        self.assertIn('<html lang="fi">', html)
        self.assertIn('href="#main-content"', html)
        self.assertIn("<nav aria-label=", html)
        self.assertIn('id="main-content"', html)
        self.assertIn('tabindex="-1"', html)

    def test_global_template_directory_is_configured(self):
        self.assertIn(settings.BASE_DIR / "templates", settings.TEMPLATES[0]["DIRS"])
        self.assertTrue((Path(settings.BASE_DIR) / "templates" / "base.html").is_file())
