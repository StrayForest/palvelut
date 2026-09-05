from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.discovery.services import rebuild_provider_read_document
from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.publishing.models import ProfileRevision

from .claim_services import resolve_provider_claim, submit_provider_claim
from .models import Provider, ProviderMembership
from .team_models import ProviderInvitation
from .team_services import accept_invitation, invite_editor, transfer_ownership

TEST_PASSWORD = "Strong-passphrase-2026!"  # test-only


class AtomicProviderAcceptanceTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.claimant = user_model.objects.create_user(
            username="atomic-claimant@example.com",
            email="atomic-claimant@example.com",
            password=TEST_PASSWORD,
        )
        self.editor = user_model.objects.create_user(
            username="atomic-editor@example.com",
            email="atomic-editor@example.com",
            password=TEST_PASSWORD,
        )
        self.staff = user_model.objects.create_user(
            username="atomic-staff@example.com",
            email="atomic-staff@example.com",
            password=TEST_PASSWORD,
            is_staff=True,
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.UNCLAIMED,
            claim_status=Provider.ClaimStatus.UNCLAIMED,
            legal_name="Atomic Provider Oy",
            display_name="Atomic Provider",
            y_tunnus="2468135-7",
        )

    def _submit_claim(self) -> None:
        submit_provider_claim(
            provider_id=self.provider.pk,
            actor=self.claimant,
            evidence_kind="registry_signatory",
            evidence_reference="PRH signatory record",
        )

    def _approve_claim(self) -> None:
        self._submit_claim()
        resolve_provider_claim(
            provider_id=self.provider.pk,
            actor=self.staff,
            decision="approve",
            review_note="Independent control evidence confirmed.",
        )

    def test_claim_approval_rolls_back_if_audit_write_fails(self) -> None:
        self._submit_claim()

        with patch.object(AuditEvent.objects, "create", side_effect=RuntimeError("audit failed")):
            with self.assertRaises(RuntimeError):
                resolve_provider_claim(
                    provider_id=self.provider.pk,
                    actor=self.staff,
                    decision="approve",
                    review_note="Would otherwise approve.",
                )

        self.provider.refresh_from_db()
        self.assertEqual(self.provider.claim_status, Provider.ClaimStatus.PENDING)
        self.assertEqual(self.provider.lifecycle, Provider.Lifecycle.UNCLAIMED)
        self.assertFalse(
            ProviderMembership.objects.filter(provider=self.provider).exists()
        )

    def test_claim_rejection_rolls_back_if_audit_write_fails(self) -> None:
        self._submit_claim()

        with patch.object(AuditEvent.objects, "create", side_effect=RuntimeError("audit failed")):
            with self.assertRaises(RuntimeError):
                resolve_provider_claim(
                    provider_id=self.provider.pk,
                    actor=self.staff,
                    decision="reject",
                    review_note="Would otherwise reject.",
                )

        self.provider.refresh_from_db()
        self.assertEqual(self.provider.claim_status, Provider.ClaimStatus.PENDING)
        self.assertEqual(self.provider.lifecycle, Provider.Lifecycle.UNCLAIMED)
        self.assertNotEqual(self.provider.claim_evidence.get("decision"), "reject")

    def test_membership_acceptance_rolls_back_if_audit_write_fails(self) -> None:
        self._approve_claim()
        invitation = invite_editor(
            provider=self.provider,
            actor=self.claimant,
            invited_account=self.editor,
        )

        with patch.object(AuditEvent.objects, "create", side_effect=RuntimeError("audit failed")):
            with self.assertRaises(RuntimeError):
                accept_invitation(invitation=invitation, actor=self.editor)

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, ProviderInvitation.Status.PENDING)
        self.assertIsNone(invitation.accepted_at)
        self.assertFalse(
            ProviderMembership.objects.filter(
                provider=self.provider,
                account=self.editor,
            ).exists()
        )

    def test_ownership_transfer_rolls_back_if_audit_write_fails(self) -> None:
        self._approve_claim()
        invitation = invite_editor(
            provider=self.provider,
            actor=self.claimant,
            invited_account=self.editor,
        )
        accept_invitation(invitation=invitation, actor=self.editor)

        with patch.object(AuditEvent.objects, "create", side_effect=RuntimeError("audit failed")):
            with self.assertRaises(RuntimeError):
                transfer_ownership(
                    provider=self.provider,
                    actor=self.claimant,
                    target_account=self.editor,
                )

        owner_membership = ProviderMembership.objects.get(
            provider=self.provider,
            account=self.claimant,
        )
        editor_membership = ProviderMembership.objects.get(
            provider=self.provider,
            account=self.editor,
        )
        self.assertEqual(owner_membership.role, ProviderMembership.Role.OWNER)
        self.assertEqual(editor_membership.role, ProviderMembership.Role.EDITOR)
        self.assertEqual(
            ProviderMembership.objects.filter(
                provider=self.provider,
                role=ProviderMembership.Role.OWNER,
                is_active=True,
            ).count(),
            1,
        )

    def test_approved_claim_and_team_changes_cannot_publish_unapproved_profile(self) -> None:
        self._approve_claim()
        invitation = invite_editor(
            provider=self.provider,
            actor=self.claimant,
            invited_account=self.editor,
        )
        accept_invitation(invitation=invitation, actor=self.editor)
        transfer_ownership(
            provider=self.provider,
            actor=self.claimant,
            target_account=self.editor,
        )

        self.provider.refresh_from_db()
        self.assertEqual(self.provider.lifecycle, Provider.Lifecycle.DRAFT)
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=self.provider,
                actor=self.staff,
                action="provider.claim_approved",
            ).exists()
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=self.provider,
                action="provider.membership.accepted",
            ).exists()
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=self.provider,
                action="provider.ownership.transferred",
            ).exists()
        )

        ProfileRevision.objects.create(
            provider=self.provider,
            status=ProfileRevision.Status.APPROVED,
            payload={"display_name": "Atomic Provider"},
            created_by=self.staff,
        )
        with self.assertRaises(ValidationError):
            rebuild_provider_read_document(provider_id=self.provider.pk)
        self.assertFalse(
            ProviderReadDocument.objects.filter(provider=self.provider).exists()
        )
