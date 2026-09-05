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
            "No visitor identity, IP address, search text, or cross-site identifier is stored or shown.",
            template,
        )
        self.assertIn(
            "times this provider appears in anonymous public discovery results.",
            template,
        )
        self.assertIn(
            "anonymous public opens of this provider profile.",
            template,
        )
        self.assertIn(
            "tracked clicks from this provider profile to a public contact channel.",
            template,
        )
