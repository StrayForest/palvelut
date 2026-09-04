import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import ContactChannel, Provider


class StaffBackOfficeCompletionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="staff-backoffice",
            email="staff-backoffice@example.invalid",
            password="test-only-password",
        )
        self.client.force_login(self.user)

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

    def test_merge_deduplicates_same_contact_on_canonical_provider(self):
        target = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Canonical Contact Oy",
            display_name="Canonical Contact",
        )
        duplicate = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Duplicate Contact Oy",
            display_name="Duplicate Contact",
        )
        for provider in (target, duplicate):
            ContactChannel.objects.create(
                provider=provider,
                kind=ContactChannel.Kind.EMAIL,
                value="shared@example.invalid",
            )

        response = self.client.post(
            reverse("admin:providers_provider_changelist"),
            {
                "action": "merge_duplicates",
                "_selected_action": [str(duplicate.pk), str(target.pk)],
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        duplicate.refresh_from_db()
        self.assertEqual(duplicate.lifecycle, Provider.Lifecycle.ARCHIVED)
        self.assertEqual(
            ContactChannel.objects.filter(
                provider=target,
                kind=ContactChannel.Kind.EMAIL,
                value="shared@example.invalid",
            ).count(),
            1,
        )
