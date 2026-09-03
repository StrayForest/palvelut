from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.moderation.services import moderate_provider
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision


class StaffModerationServiceTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="moderator",
            password="not-used",
            is_staff=True,
        )
        self.user = user_model.objects.create_user(
            username="provider-user",
            password="not-used",
        )

    def _provider(self, *, claimed: bool = True) -> Provider:
        return Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Example Oy",
            display_name="Example",
            claim_status=(
                Provider.ClaimStatus.APPROVED if claimed else Provider.ClaimStatus.UNCLAIMED
            ),
        )

    def _revision(self, provider: Provider) -> ProfileRevision:
        return ProfileRevision.objects.create(
            provider=provider,
            status=ProfileRevision.Status.PENDING,
            payload={"display_name": "Example updated"},
            created_by=self.staff,
        )

    def test_staff_can_approve_claimed_provider_and_revision(self) -> None:
        provider = self._provider()
        revision = self._revision(provider)

        result = moderate_provider(provider_id=provider.pk, actor=self.staff, action="approve")

        provider.refresh_from_db()
        revision.refresh_from_db()
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.PUBLISHED)
        self.assertEqual(revision.status, ProfileRevision.Status.APPROVED)
        self.assertIsNotNone(revision.reviewed_at)
        self.assertEqual(result.revision_id, revision.pk)
        audit = AuditEvent.objects.get(provider=provider, action="provider.approved")
        self.assertEqual(audit.actor, self.staff)
        self.assertEqual(audit.metadata["revision_id"], str(revision.pk))

    def test_unclaimed_provider_cannot_be_approved(self) -> None:
        provider = self._provider(claimed=False)
        revision = self._revision(provider)

        with self.assertRaisesMessage(ValidationError, "Only an approved claim can be published"):
            moderate_provider(provider_id=provider.pk, actor=self.staff, action="approve")

        provider.refresh_from_db()
        revision.refresh_from_db()
        self.assertNotEqual(provider.lifecycle, Provider.Lifecycle.PUBLISHED)
        self.assertEqual(revision.status, ProfileRevision.Status.PENDING)

    def test_request_changes_updates_revision_and_provider_with_audit(self) -> None:
        provider = self._provider()
        revision = self._revision(provider)

        moderate_provider(provider_id=provider.pk, actor=self.staff, action="request_changes")

        provider.refresh_from_db()
        revision.refresh_from_db()
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.CHANGES_REQUESTED)
        self.assertEqual(revision.status, ProfileRevision.Status.CHANGES_REQUESTED)
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=provider,
                actor=self.staff,
                action="provider.changes_requested",
            ).exists()
        )

    def test_suspend_records_previous_lifecycle(self) -> None:
        provider = self._provider()
        provider.lifecycle = Provider.Lifecycle.PENDING
        provider.save(update_fields=("lifecycle", "updated_at"))

        moderate_provider(provider_id=provider.pk, actor=self.staff, action="suspend")

        provider.refresh_from_db()
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.SUSPENDED)
        event = AuditEvent.objects.get(provider=provider, action="provider.suspended")
        self.assertEqual(event.metadata["previous_lifecycle"], Provider.Lifecycle.PENDING)

    def test_non_staff_cannot_moderate(self) -> None:
        provider = self._provider()
        self._revision(provider)

        with self.assertRaises(PermissionDenied):
            moderate_provider(provider_id=provider.pk, actor=self.user, action="approve")


class StaffAdminRegistrationTests(TestCase):
    def test_provider_and_revision_are_registered(self) -> None:
        self.assertIn(Provider, admin.site._registry)
        self.assertIn(ProfileRevision, admin.site._registry)
