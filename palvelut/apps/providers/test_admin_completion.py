import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import (
    ContactChannel,
    Provider,
    ProviderMembership,
)
from palvelut.apps.publishing.models import ProfileRevision


class StaffBackOfficeCompletionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="staff-backoffice",
            email="staff-backoffice@example.invalid",
            password="test-only-password",
        )
        self.client.force_login(self.user)

    def test_owner_confirmed_provider_can_be_created_and_published_in_admin(self):
        owner = get_user_model().objects.create_user(
            username="provider-owner",
            password="test-only-password",
        )

        response = self.client.post(
            reverse("admin:providers_provider_owner_confirmed_add"),
            {
                "provider_type": Provider.Type.BUSINESS,
                "legal_name": "Owner Confirmed Oy",
                "display_name": "Owner Confirmed",
                "y_tunnus": "7654321-0",
                "owner": str(owner.pk),
                "claim_evidence": json.dumps({"source": "staff-confirmed"}),
                "revision_payload": json.dumps({"summary": "Approved profile"}),
                "publish_now": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        provider = Provider.objects.get(y_tunnus="7654321-0")
        self.assertEqual(provider.claim_status, Provider.ClaimStatus.APPROVED)
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.PUBLISHED)
        self.assertTrue(
            ProviderMembership.objects.filter(
                provider=provider,
                account=owner,
                role=ProviderMembership.Role.OWNER,
                is_active=True,
            ).exists()
        )
        self.assertTrue(
            ProfileRevision.objects.filter(
                provider=provider,
                status=ProfileRevision.Status.APPROVED,
            ).exists()
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=provider,
                actor=self.user,
                action="provider.owner_confirmed_created",
            ).exists()
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=provider,
                actor=self.user,
                action="provider.approved",
            ).exists()
        )

    def test_import_is_idempotent_and_audited(self):
        url = reverse("admin:providers_provider_import")
        records = [
            {
                "provider_type": Provider.Type.BUSINESS,
                "legal_name": "Imported Oy",
                "display_name": "Imported provider",
                "y_tunnus": "1234567-8",
            }
        ]

        first = self.client.post(url, {"records": json.dumps(records)})
        second = self.client.post(url, {"records": json.dumps(records)})

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(Provider.objects.filter(y_tunnus="1234567-8").count(), 1)
        provider = Provider.objects.get(y_tunnus="1234567-8")
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.UNCLAIMED)
        self.assertEqual(provider.claim_status, Provider.ClaimStatus.UNCLAIMED)
        self.assertEqual(
            AuditEvent.objects.filter(
                provider=provider,
                actor=self.user,
                action="provider.imported",
            ).count(),
            2,
        )

    def test_import_requires_staff_permission(self):
        user = get_user_model().objects.create_user(
            username="plain-user",
            password="test-only-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("admin:providers_provider_import"))

        self.assertIn(response.status_code, (302, 403))

    def test_merge_uses_oldest_provider_as_canonical_and_audits(self):
        target = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Canonical Oy",
            display_name="Canonical",
        )
        duplicate = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Duplicate Oy",
            display_name="Duplicate",
        )
        ContactChannel.objects.create(
            provider=duplicate,
            kind=ContactChannel.Kind.EMAIL,
            value="duplicate@example.invalid",
        )

        response = self.client.post(
            reverse("admin:providers_provider_changelist"),
            {
                "action": "merge_duplicates",
                "_selected_action": [str(target.pk), str(duplicate.pk)],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        duplicate.refresh_from_db()
        self.assertEqual(duplicate.lifecycle, Provider.Lifecycle.ARCHIVED)
        self.assertTrue(
            ContactChannel.objects.filter(
                provider=target,
                value="duplicate@example.invalid",
            ).exists()
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=target,
                actor=self.user,
                action="provider.duplicates_merged",
            ).exists()
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=duplicate,
                actor=self.user,
                action="provider.merged_into",
            ).exists()
        )
