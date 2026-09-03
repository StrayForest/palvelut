from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.providers.services import merge_duplicate_pair, suspend_provider
from palvelut.apps.publishing.models import ProfileRevision
from palvelut.apps.publishing.services import approve_revision, request_revision_changes, revision_diff
from palvelut.apps.verification.models import ProviderClaim
from palvelut.apps.verification.services import approve_claim


@override_settings(ALLOWED_HOSTS=["testserver"])
class StaffAdminWorkflowTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="staff",
            password="test-only-password",
            is_staff=True,
            is_superuser=True,
        )
        self.owner = user_model.objects.create_user(
            username="owner",
            password="test-only-password",
        )

    def create_provider(self, *, lifecycle: str = Provider.Lifecycle.UNCLAIMED) -> Provider:
        return Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=lifecycle,
            legal_name="Example Oy",
            display_name="Example",
        )

    def test_staff_admin_is_staff_only_and_not_cacheable(self) -> None:
        client = Client()
        anonymous = client.get("/palvelut/staff/")
        self.assertEqual(anonymous.status_code, 302)
        self.assertIn("/palvelut/staff/login/", anonymous["Location"])

        client.force_login(self.staff)
        response = client.get("/palvelut/staff/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response.get("Cache-Control", ""))

    def test_unclaimed_import_cannot_publish_until_claim_is_approved(self) -> None:
        provider = self.create_provider()
        revision = ProfileRevision.objects.create(
            provider=provider,
            status=ProfileRevision.Status.PENDING,
            payload={"display_name": "Claimed Example"},
            created_by=self.staff,
        )

        with self.assertRaisesMessage(ValidationError, "Unclaimed providers cannot publish"):
            approve_revision(revision=revision, actor=self.staff)

        claim = ProviderClaim.objects.create(
            provider=provider,
            claimant=self.owner,
            evidence_type=ProviderClaim.EvidenceType.REGISTRY_SIGNATORY,
            evidence_metadata={"source": "YTJ fixture", "reference": "claim-1"},
        )
        approve_claim(claim=claim, actor=self.staff)

        provider.refresh_from_db()
        claim.refresh_from_db()
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.DRAFT)
        self.assertEqual(claim.status, ProviderClaim.Status.APPROVED)
        self.assertEqual(claim.reviewed_by, self.staff)
        self.assertIsNotNone(claim.reviewed_at)
        self.assertTrue(
            ProviderMembership.objects.filter(
                provider=provider,
                account=self.owner,
                role=ProviderMembership.Role.OWNER,
                is_active=True,
            ).exists()
        )

        approve_revision(revision=revision, actor=self.staff)
        provider.refresh_from_db()
        revision.refresh_from_db()
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.PUBLISHED)
        self.assertEqual(revision.status, ProfileRevision.Status.APPROVED)
        self.assertIsNotNone(revision.reviewed_at)
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=provider,
                actor=self.staff,
                action="claim.approved",
            ).exists()
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=provider,
                actor=self.staff,
                action="revision.approved",
            ).exists()
        )

    def test_owner_confirmed_staff_created_provider_can_publish(self) -> None:
        provider = self.create_provider(lifecycle=Provider.Lifecycle.DRAFT)
        ProviderMembership.objects.create(
            provider=provider,
            account=self.owner,
            role=ProviderMembership.Role.OWNER,
            is_active=True,
        )
        revision = ProfileRevision.objects.create(
            provider=provider,
            status=ProfileRevision.Status.PENDING,
            payload={"display_name": "Owner confirmed"},
            created_by=self.staff,
        )

        approve_revision(revision=revision, actor=self.staff)

        provider.refresh_from_db()
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.PUBLISHED)

    def test_pending_edit_diff_and_changes_request_leave_approved_revision_live(self) -> None:
        provider = self.create_provider(lifecycle=Provider.Lifecycle.PUBLISHED)
        ProviderMembership.objects.create(
            provider=provider,
            account=self.owner,
            role=ProviderMembership.Role.OWNER,
            is_active=True,
        )
        approved = ProfileRevision.objects.create(
            provider=provider,
            status=ProfileRevision.Status.APPROVED,
            payload={"display_name": "Old", "city": "Helsinki"},
            created_by=self.staff,
        )
        pending = ProfileRevision.objects.create(
            provider=provider,
            status=ProfileRevision.Status.PENDING,
            payload={"display_name": "New", "city": "Helsinki"},
            created_by=self.owner,
        )

        self.assertEqual(
            revision_diff(pending),
            {"display_name": {"before": "Old", "after": "New"}},
        )
        request_revision_changes(revision=pending, actor=self.staff)

        approved.refresh_from_db()
        pending.refresh_from_db()
        provider.refresh_from_db()
        self.assertEqual(approved.status, ProfileRevision.Status.APPROVED)
        self.assertEqual(pending.status, ProfileRevision.Status.CHANGES_REQUESTED)
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.CHANGES_REQUESTED)

    def test_suspend_and_duplicate_merge_are_audited_and_deterministic(self) -> None:
        first = self.create_provider(lifecycle=Provider.Lifecycle.DRAFT)
        first.display_name = "First"
        first.save(update_fields=("display_name", "updated_at"))
        second = self.create_provider(lifecycle=Provider.Lifecycle.DRAFT)
        second.display_name = "Second"
        second.save(update_fields=("display_name", "updated_at"))

        suspended = suspend_provider(provider=second, actor=self.staff, reason="policy")
        self.assertEqual(suspended.lifecycle, Provider.Lifecycle.SUSPENDED)

        survivor = merge_duplicate_pair(first=second, second=first, actor=self.staff)
        expected_survivor_id = min(first.pk, second.pk)
        self.assertEqual(survivor.pk, expected_survivor_id)

        first.refresh_from_db()
        second.refresh_from_db()
        archived = second if survivor.pk == first.pk else first
        self.assertEqual(archived.lifecycle, Provider.Lifecycle.ARCHIVED)
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=survivor,
                actor=self.staff,
                action="provider.duplicate_merged",
            ).exists()
        )
