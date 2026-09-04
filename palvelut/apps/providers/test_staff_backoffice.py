from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import ContactChannel, Provider, ProviderMembership
from palvelut.apps.providers.services import (
    import_unclaimed_provider,
    merge_duplicate_providers,
)


class StaffBackOfficeTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="staff-backoffice",
            password="test-password-only",
            is_staff=True,
        )
        self.regular = user_model.objects.create_user(
            username="regular-backoffice",
            password="test-password-only",
        )

    def test_import_is_staff_only_idempotent_and_non_public(self) -> None:
        data = {
            "provider_type": Provider.Type.BUSINESS,
            "legal_name": "Example Oy",
            "display_name": "Example",
            "y_tunnus": "1234567-8",
        }
        with self.assertRaises(ValidationError):
            import_unclaimed_provider(actor=self.regular, data=data)

        first = import_unclaimed_provider(actor=self.staff, data=data)
        second = import_unclaimed_provider(
            actor=self.staff,
            data={**data, "display_name": "Example Updated"},
        )

        self.assertEqual(first.pk, second.pk)
        second.refresh_from_db()
        self.assertEqual(second.lifecycle, Provider.Lifecycle.UNCLAIMED)
        self.assertEqual(second.claim_status, Provider.ClaimStatus.UNCLAIMED)
        self.assertEqual(second.display_name, "Example Updated")
        self.assertFalse(ProviderMembership.objects.filter(provider=second).exists())
        self.assertEqual(
            AuditEvent.objects.filter(provider=second, actor=self.staff).count(),
            2,
        )

    def test_merge_moves_unique_rows_archives_source_and_audits(self) -> None:
        target = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.UNCLAIMED,
            legal_name="Canonical Oy",
            display_name="Canonical",
            y_tunnus="7654321-0",
        )
        source = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.UNCLAIMED,
            legal_name="Duplicate",
            display_name="Duplicate",
        )
        contact = ContactChannel.objects.create(
            provider=source,
            kind=ContactChannel.Kind.EMAIL,
            value="hello@example.invalid",
        )

        merged = merge_duplicate_providers(
            actor=self.staff,
            target_id=target.pk,
            source_id=source.pk,
        )

        self.assertEqual(merged.pk, target.pk)
        contact.refresh_from_db()
        source.refresh_from_db()
        self.assertEqual(contact.provider_id, target.pk)
        self.assertEqual(source.lifecycle, Provider.Lifecycle.ARCHIVED)
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=target,
                actor=self.staff,
                action="provider.duplicates_merged",
            ).exists()
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=source,
                actor=self.staff,
                action="provider.merged_into",
            ).exists()
        )

    def test_merge_rejects_conflicting_y_tunnus(self) -> None:
        target = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="One Oy",
            display_name="One",
            y_tunnus="1111111-1",
        )
        source = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Two Oy",
            display_name="Two",
            y_tunnus="2222222-2",
        )

        with self.assertRaises(ValidationError):
            merge_duplicate_providers(
                actor=self.staff,
                target_id=target.pk,
                source_id=source.pk,
            )
