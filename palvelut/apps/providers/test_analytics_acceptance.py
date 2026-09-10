from pathlib import Path

from django.test import SimpleTestCase

from palvelut.apps.analytics.models import AnalyticsEvent


class ProviderAnalyticsAcceptanceTests(SimpleTestCase):
    def test_analytics_event_schema_has_no_visitor_identity_fields(self):
        concrete_fields = {
            field.name
            for field in AnalyticsEvent._meta.get_fields()
            if getattr(field, "concrete", False)
        }
        self.assertEqual(
            concrete_fields,
            {"id", "kind", "provider", "channel", "occurred_at"},
        )

    def test_workspace_exposes_metric_definitions_and_privacy_boundary(self):
        template = Path("templates/providers/workspace.html").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "Мы не показываем и не сохраняем здесь личность посетителя, IP-адрес, текст поиска или межсайтовый идентификатор.",
            template,
        )
        self.assertIn(
            "Сколько раз карточка появилась в обезличенных публичных результатах поиска.",
            template,
        )
        self.assertIn(
            "Сколько раз посетители открыли эту карточку в публичном каталоге.",
            template,
        )
        self.assertIn(
            "Сколько раз посетители перешли из карточки к публичному способу связи.",
            template,
        )
