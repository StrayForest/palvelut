from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from palvelut.apps.providers.access_audit import ProviderAccessAudit
from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.publishing.models import ProfileRevision


class CrossProviderAccessAuditTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="owner-a@example.test",
            email="owner-a@example.test",
            password="test-only-pass",
        )
        self.other = user_model.objects.create_user(
            username="owner-b@example.test",
            email="owner-b@example.test",
            password="test-only-pass",
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.DRAFT,
            claim_status=Provider.ClaimStatus.APPROVED,
            legal_name="Protected Oy",
            display_name="Protected",
            y_tunnus="7654321-0",
        )
        ProviderMembership.objects.create(
            provider=self.provider,
            account=self.owner,
            role=ProviderMembership.Role.OWNER,
        )
        self.client.force_login(self.other)

    def _assert_denied_and_audited(self, response, *, method: str, path: str):
        self.assertEqual(response.status_code, 404)
        audit = ProviderAccessAudit.objects.get()
        self.assertEqual(audit.actor, self.other)
        self.assertEqual(audit.target_provider_id, self.provider.pk)
        self.assertEqual(audit.method, method)
        self.assertEqual(audit.path, path)
        self.assertEqual(audit.outcome, ProviderAccessAudit.Outcome.DENIED)

    def test_cross_provider_read_is_hidden_and_audited(self):
        path = reverse("provider-workspace-preview", args=[self.provider.pk])
        response = self.client.get(path)
        self._assert_denied_and_audited(response, method="GET", path=path)
        self.assertFalse(ProfileRevision.objects.filter(provider=self.provider).exists())

    def test_cross_provider_write_is_hidden_audited_and_does_not_mutate(self):
        path = reverse("provider-workspace-edit", args=[self.provider.pk])
        response = self.client.post(
            path,
            {
                "provider_type": "business",
                "legal_name": "Attacker Oy",
                "display_name": "Attacker",
                "y_tunnus": "",
            },
        )
        self._assert_denied_and_audited(response, method="POST", path=path)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.legal_name, "Protected Oy")
        self.assertEqual(self.provider.display_name, "Protected")
        self.assertFalse(ProfileRevision.objects.filter(provider=self.provider).exists())

    def test_denials_are_independently_audited_for_sensitive_actions(self):
        preview_path = reverse("provider-workspace-preview", args=[self.provider.pk])
        upload_path = reverse("provider-workspace-upload", args=[self.provider.pk])
        submit_path = reverse("provider-workspace-submit", args=[self.provider.pk])

        self.assertEqual(self.client.get(preview_path).status_code, 404)
        self.assertEqual(self.client.post(upload_path).status_code, 404)
        self.assertEqual(self.client.post(submit_path).status_code, 404)

        rows = list(
            ProviderAccessAudit.objects.order_by("created_at").values_list(
                "method", "path", "outcome"
            )
        )
        self.assertEqual(
            rows,
            [
                ("GET", preview_path, "denied"),
                ("POST", upload_path, "denied"),
                ("POST", submit_path, "denied"),
            ],
        )
