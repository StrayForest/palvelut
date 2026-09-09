from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class ProviderSurfaceContractTests(TestCase):
    def test_public_provider_auth_surfaces_expose_workspace_navigation(self):
        login = self.client.get(reverse("account-login"))
        self.assertContains(login, reverse("provider-workspace"))
        self.assertContains(login, "Provider workspace")
        self.assertContains(login, "What happens next")

        register = self.client.get(reverse("account-register"))
        self.assertContains(register, reverse("provider-workspace"))
        self.assertContains(register, "Ownership approval unlocks profile editing")

    def test_empty_workspace_leads_with_status_and_single_next_action(self):
        user = get_user_model().objects.create_user(
            username="surface-contract@example.test",
            email="surface-contract@example.test",
            password="surface-contract-pass",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("provider-workspace"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "private, no-store")
        self.assertContains(response, 'data-workspace-status="not-started"')
        self.assertContains(response, "Current status")
        self.assertContains(response, "Next action")
        self.assertContains(response, reverse("account-provider-start"))
        self.assertContains(response, reverse("account-claim-list"))

    def test_provider_surface_ui_strings_are_marked_for_localization(self):
        repository_root = Path(__file__).resolve().parents[3]
        for relative_path in (
            "templates/accounts/login.html",
            "templates/accounts/register.html",
            "templates/providers/start_provider.html",
            "templates/providers/workspace.html",
        ):
            source = (repository_root / relative_path).read_text(encoding="utf-8")
            self.assertIn("{% load i18n %}", source)
            self.assertIn("{% translate", source)

        account_forms = (
            repository_root / "palvelut/apps/accounts/forms.py"
        ).read_text(encoding="utf-8")
        claim_forms = (
            repository_root / "palvelut/apps/providers/claim_forms.py"
        ).read_text(encoding="utf-8")
        self.assertIn("gettext_lazy as _", account_forms)
        self.assertIn("gettext_lazy as _", claim_forms)
