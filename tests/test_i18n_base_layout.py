from pathlib import Path
from unittest import TestCase

import django
from django.conf import settings
from django.template.loader import render_to_string


django.setup()


class RussianOnlyBaseLayoutContractTests(TestCase):
    def test_only_russian_ui_locale_is_supported(self):
        self.assertEqual(settings.LANGUAGE_CODE, "ru")
        self.assertEqual([code for code, _ in settings.LANGUAGES], ["ru"])
        self.assertNotIn(
            "django.middleware.locale.LocaleMiddleware", settings.MIDDLEWARE
        )
        self.assertFalse(settings.is_overridden("LOCALE_PATHS"))

    def test_base_template_has_accessibility_landmarks_and_russian_registration(self):
        html = render_to_string("base.html")

        self.assertIn('<html lang="ru">', html)
        self.assertIn('href="#main-content"', html)
        self.assertIn('aria-label="Основная навигация"', html)
        self.assertIn('id="main-content"', html)
        self.assertIn('tabindex="-1"', html)
        self.assertIn("Разместить карточку", html)
        self.assertNotIn("For professionals", html)
        self.assertNotIn("Sign in", html)

    def test_global_template_directory_is_configured(self):
        self.assertIn(settings.BASE_DIR / "templates", settings.TEMPLATES[0]["DIRS"])
        self.assertTrue((Path(settings.BASE_DIR) / "templates" / "base.html").is_file())
