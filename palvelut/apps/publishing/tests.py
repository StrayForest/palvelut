from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.verification.models import ProviderClaim
from palvelut.apps.verification.services import approve_claim

from .models import ProfileRevision
from .services import approve_revision, merge_duplicate, suspend_provider


class StaffWorkflowTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_superuser(
            username="staff",
            email="staff@example.invalid",
            password="test-password",  # test-only
        )
        self.owner = user_model.objects.create_user(username="owner")
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.INDIVIDUAL,
            legal_name="Imported Person",
            display_name="Imported Person",
            lifecycle=Provider.Lifecycle.UNCLAIMED,
        )
        self.revision = ProfileRevision.objects.create(
            provider=self.provider,
            created_by=self.staff,
            status=ProfileRevision.Status.PENDING,
            payload={"display_name": "Imported Person"},
        )

    def test_unclaimed_provider_cannot_publish_without_approved_claim(self) -> None:
        with self.assertRaisesMessage(
            ValidationError,
            "Provider requires an approved claim before publishing.",
        ):
            approve_revision(revision=self.revision, actor=self.staff)

        self.provider.refresh_from_db()
        self.revision.refresh_from_db()
        self.assertEqual(self.provider.lifecycle, Provider.Lifecycle.UNCLAIMED)
        self.assertEqual(self.revision.status, ProfileRevision.Status.PENDING)

    def test_approved_claim_grants_owner_and_allows_publish(self) -> None:
        claim = ProviderClaim.objects.create(
            provider=self.provider,
            claimed_by=self.owner,
            evidence_metadata={"method": "staff-confirmed"},
        )
        approve_claim(claim=claim, actor=self.staff)
        approve_revision(revision=self.revision, actor=self.staff)

        self.provider.refresh_from_db()
        claim.refresh_from_db()
        self.revision.refresh_from_db()
        membership = ProviderMembership.objects.get(
            provider=self.provider,
            account=self.owner,
        )
        self.assertEqual(claim.status, ProviderClaim.Status.APPROVED)
        self.assertEqual(claim.reviewed_by, self.staff)
        self.assertIsNotNone(claim.reviewed_at)
        self.assertEqual(membership.role, ProviderMembership.Role.OWNER)
        self.assertTrue(membership.is_active)
        self.assertEqual(self.provider.lifecycle, Provider.Lifecycle.PUBLISHED)
        self.assertEqual(self.revision.status, ProfileRevision.Status.APPROVED)
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=self.provider,
                action="provider.claim.approved",
                actor=self.staff,
            ).exists()
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=self.provider,
                action="provider.revision.approved",
                actor=self.staff,
            ).exists()
        )

    def test_suspend_and_duplicate_merge_are_audited(self) -> None:
        canonical = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Canonical Oy",
            display_name="Canonical",
            lifecycle=Provider.Lifecycle.PUBLISHED,
        )
        suspend_provider(provider=canonical, actor=self.staff)
        merge_duplicate(source=self.provider, target=canonical, actor=self.staff)

        canonical.refresh_from_db()
        self.provider.refresh_from_db()
        self.assertEqual(canonical.lifecycle, Provider.Lifecycle.SUSPENDED)
        self.assertEqual(self.provider.lifecycle, Provider.Lifecycle.ARCHIVED)
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=self.provider,
                action="provider.duplicate.merged",
                actor=self.staff,
            ).exists()
        )


class StaffAdminPermissionTests(TestCase):
    def test_admin_requires_staff_permission(self) -> None:
        user_model = get_user_model()
        regular = user_model.objects.create_user(
            username="regular",
            password="test-password",  # test-only
        )
        staff = user_model.objects.create_superuser(
            username="admin",
            email="admin@example.invalid",
            password="test-password",  # test-only
        )

        self.client.force_login(regular)
        response = self.client.get("/palvelut/admin/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/palvelut/admin/login/", response["Location"])

        self.client.force_login(staff)
        response = self.client.get("/palvelut/admin/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["Cache-Control"],
            "max-age=0, no-cache, no-store, must-revalidate, private",
        )
