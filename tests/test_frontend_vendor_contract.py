import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FrontendVendorContractTests(unittest.TestCase):
    def test_interaction_dependencies_are_exactly_pinned(self):
        package = json.loads((ROOT / "frontend" / "package.json").read_text())
        self.assertEqual(package["dependencies"]["htmx.org"], "2.0.4")
        self.assertEqual(package["dependencies"]["alpinejs"], "3.14.8")

    def test_app_image_vendors_both_libraries_without_runtime_cdn(self):
        dockerfile = (ROOT / "Dockerfile").read_text()
        self.assertIn("node_modules/htmx.org/dist/htmx.min.js", dockerfile)
        self.assertIn("node_modules/alpinejs/dist/cdn.min.js", dockerfile)
        self.assertIn("COPY --from=frontend /frontend-dist ./static", dockerfile)
        self.assertNotIn("unpkg.com", dockerfile)
        self.assertNotIn("cdn.jsdelivr.net", dockerfile)

    def test_django_staticfiles_discovers_generated_vendor_directory(self):
        settings = (ROOT / "palvelut" / "settings.py").read_text()
        self.assertIn('STATICFILES_DIRS = [BASE_DIR / "static"]', settings)


if __name__ == "__main__":
    unittest.main()
