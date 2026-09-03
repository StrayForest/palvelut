import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision


class StaffAdminTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="staff-admin",
            email="staff@example.invalid",
            password="test-only-password",
        )
        self.client.force_login(self.user)

    def _provider(self, name="Example Provider"):
        return Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name=name,
            display_name=name,
        )

    def test_provider_import_is_staff_only_and_audited(self):
        url = reverse("admin:providers_provider_import")
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.user)
        records = [
            {
                "provider_type": "business",
                "legal_name": "Imported Oy",
                "display_name": "Imported",
                "y_tunnus": "1234567-8",
            }
        ]
        response = self.client.post(url, {"records": json.dumps(records)})
        self.assertEqual(response.status_code, 302)
        provider = Provider.objects.get(y_tunnus="1234567-8")
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.UNCLAIMED)
        self.assertEqual(provider.claim_status, Provider.ClaimStatus.UNCLAIMED)
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=provider,
                actor=self.user,
                action="provider.imported",
            ).exists()
        )

    def test_provider_approve_action_publishes_and_audits(self):
        provider = self._provider()
        url = reverse("admin:providers_provider_changelist")
        response = self.client.post(
            url,
            {
                "action": "approve_selected",
                "_selected_action": [str(provider.pk)],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        provider.refresh_from_db()
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.PUBLISHED)
        self.assertEqual(provider.claim_status, Provider.ClaimStatus.APPROVED)
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=provider,
                actor=self.user,
                action="provider.approved",
            ).exists()
        )

    def test_revision_approval_applies_payload_and_records_actor(self):
        provider = self._provider()
        revision = ProfileRevision.objects.create(
            provider=provider,
            created_by=self.user,
            status=ProfileRevision.Status.PENDING,
            payload={"display_name": "Reviewed name"},
        )
        url = reverse("admin:publishing_profilerevision_changelist")
        response = self.client.post(
            url,
            {
                "action": "approve_revisions",
                "_selected_action": [str(revision.pk)],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        provider.refresh_from_db()
        revision.refresh_from_db()
        self.assertEqual(provider.display_name, "Reviewed name")
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.PUBLISHED)
        self.assertEqual(revision.status, ProfileRevision.Status.APPROVED)
        self.assertIsNotNone(revision.reviewed_at)
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=provider,
                actor=self.user,
                action="profile_revision.approved",
            ).exists()
        )
