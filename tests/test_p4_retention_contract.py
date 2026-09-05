from pathlib import Path

from django.test import SimpleTestCase


class P4RetentionContractTests(SimpleTestCase):
    def test_quality_contract_and_runtime_retention_stay_aligned(self):
        quality = Path("docs/06-quality.md").read_text(encoding="utf-8")
        task = Path("palvelut/apps/analytics/tasks.py").read_text(encoding="utf-8")
        settings = Path("palvelut/settings.py").read_text(encoding="utf-8")

        self.assertIn("Raw analytics expire after 90 days", quality)
        self.assertIn("ANALYTICS_RETENTION_DAYS = 90", task)
        self.assertIn('"purge-expired-analytics"', settings)
        self.assertIn('"palvelut.analytics.purge_expired"', settings)
