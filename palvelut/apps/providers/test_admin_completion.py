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

    def test_staff_can_create_and_publish_owner_confirmed_provider(self):
        owner = get_user_model().objects.create_user(
            username="provider-owner",
            email="provider-owner@example.invalid",
            password="test-only-password",
        )
        add_provider_url = reverse("admin:providers_provider_add")
        formsets = {
            "memberships": 1,
            "services": 0,
            "service_areas": 0,
            "languages": 0,
            "contacts": 0,
            "media_assets": 0,
        }
        provider_post = {
            "provider_type": Provider.Type.BUSINESS,
            "claim_status": Provider.ClaimStatus.APPROVED,
            "claim_evidence": json.dumps(
                {"method": "staff_owner_confirmation", "reference": "case-11"}
            ),
            "legal_name": "Owner Confirmed Oy",
            "display_name": "Owner Confirmed",
            "y_tunnus": "7654321-0",
            "memberships-0-account": str(owner.pk),
            "memberships-0-role": ProviderMembership.Role.OWNER,
            "memberships-0-is_active": "on",
            "_save": "Save",
        }
        for prefix, total_forms in formsets.items():
            provider_post[f"{prefix}-TOTAL_FORMS"] = str(total_forms)
            provider_post[f"{prefix}-INITIAL_FORMS"] = "0"
            provider_post[f"{prefix}-MIN_NUM_FORMS"] = "0"
            provider_post[f"{prefix}-MAX_NUM_FORMS"] = "1000"

        created = self.client.post(add_provider_url, provider_post)

        self.assertEqual(created.status_code, 302)
        provider = Provider.objects.get(y_tunnus="7654321-0")
        self.assertEqual(provider.claim_status, Provider.ClaimStatus.APPROVED)
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.UNCLAIMED)
        self.assertTrue(
            ProviderMembership.objects.filter(
                provider=provider,
                account=owner,
                role=ProviderMembership.Role.OWNER,
                is_active=True,
            ).exists()
        )

        revision_created = self.client.post(
            reverse("admin:publishing_profilerevision_add"),
            {
                "provider": str(provider.pk),
                "payload": json.dumps(
                    {
                        "display_name": provider.display_name,
                        "legal_name": provider.legal_name,
                    }
                ),
                "_save": "Save",
            },
        )
        self.assertEqual(revision_created.status_code, 302)
        revision = ProfileRevision.objects.get(provider=provider)
        self.assertEqual(revision.status, ProfileRevision.Status.PENDING)
        self.assertEqual(revision.created_by, self.user)

        published = self.client.post(
            reverse("admin:providers_provider_changelist"),
            {
                "action": "approve_selected",
                "_selected_action": [str(provider.pk)],
            },
            follow=True,
        )

        self.assertEqual(published.status_code, 200)
        provider.refresh_from_db()
        revision.refresh_from_db()
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.PUBLISHED)
        self.assertEqual(revision.status, ProfileRevision.Status.APPROVED)
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=provider,
                actor=self.user,
                action="provider.created",
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
