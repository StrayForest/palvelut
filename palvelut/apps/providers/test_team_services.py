from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from palvelut.apps.moderation.models import AuditEvent

from .models import Provider, ProviderMembership
from .team_models import ProviderInvitation
from .team_services import accept_invitation, invite_editor, transfer_ownership

TEST_PASSWORD = "Strong-passphrase-2026!"  # test-only


class ProviderTeamServicesTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="team-owner@example.com",
            email="team-owner@example.com",
            password=TEST_PASSWORD,
        )
        self.editor = user_model.objects.create_user(
            username="team-editor@example.com",
            email="team-editor@example.com",
            password=TEST_PASSWORD,
        )
        self.outsider = user_model.objects.create_user(
            username="team-outsider@example.com",
            email="team-outsider@example.com",
            password=TEST_PASSWORD,
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.DRAFT,
            claim_status=Provider.ClaimStatus.APPROVED,
            legal_name="Team Provider Oy",
            display_name="Team Provider",
            y_tunnus="1234567-8",
        )
        ProviderMembership.objects.create(
            provider=self.provider,
            account=self.owner,
            role=ProviderMembership.Role.OWNER,
        )

    def test_owner_invites_editor_and_target_accepts(self) -> None:
        invitation = invite_editor(
            provider=self.provider,
            actor=self.owner,
            invited_account=self.editor,
        )
        self.assertEqual(invitation.role, ProviderMembership.Role.EDITOR)
        self.assertEqual(invitation.status, ProviderInvitation.Status.PENDING)
        self.assertFalse(
            ProviderMembership.objects.filter(
                provider=self.provider,
                account=self.editor,
            ).exists()
        )

        membership = accept_invitation(invitation=invitation, actor=self.editor)
        invitation.refresh_from_db()
        self.assertEqual(membership.role, ProviderMembership.Role.EDITOR)
        self.assertTrue(membership.is_active)
        self.assertEqual(invitation.status, ProviderInvitation.Status.ACCEPTED)
        self.assertIsNotNone(invitation.accepted_at)
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=self.provider,
                action="provider.membership.invited",
                actor=self.owner,
            ).exists()
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=self.provider,
                action="provider.membership.accepted",
                actor=self.editor,
            ).exists()
        )

    def test_outsider_cannot_invite_or_accept_another_accounts_invite(self) -> None:
        with self.assertRaises(PermissionDenied):
            invite_editor(
                provider=self.provider,
                actor=self.outsider,
                invited_account=self.editor,
            )
        invitation = invite_editor(
            provider=self.provider,
            actor=self.owner,
            invited_account=self.editor,
        )
        with self.assertRaises(PermissionDenied):
            accept_invitation(invitation=invitation, actor=self.outsider)

    def test_duplicate_pending_invitation_is_rejected(self) -> None:
        invite_editor(
            provider=self.provider,
            actor=self.owner,
            invited_account=self.editor,
        )
        with self.assertRaises(ValidationError):
            invite_editor(
                provider=self.provider,
                actor=self.owner,
                invited_account=self.editor,
            )
        self.assertEqual(
            ProviderInvitation.objects.filter(
                provider=self.provider,
                invited_account=self.editor,
                status=ProviderInvitation.Status.PENDING,
            ).count(),
            1,
        )

    def test_transfer_requires_active_member_and_keeps_exactly_one_owner(self) -> None:
        with self.assertRaises(ValidationError):
            transfer_ownership(
                provider=self.provider,
                actor=self.owner,
                target_account=self.editor,
            )

        invitation = invite_editor(
            provider=self.provider,
            actor=self.owner,
            invited_account=self.editor,
        )
        accept_invitation(invitation=invitation, actor=self.editor)
        transfer_ownership(
            provider=self.provider,
            actor=self.owner,
            target_account=self.editor,
        )

        owner_membership = ProviderMembership.objects.get(
            provider=self.provider,
            account=self.owner,
        )
        editor_membership = ProviderMembership.objects.get(
            provider=self.provider,
            account=self.editor,
        )
        self.assertEqual(owner_membership.role, ProviderMembership.Role.EDITOR)
        self.assertEqual(editor_membership.role, ProviderMembership.Role.OWNER)
        self.assertEqual(
            ProviderMembership.objects.filter(
                provider=self.provider,
                role=ProviderMembership.Role.OWNER,
                is_active=True,
            ).count(),
            1,
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=self.provider,
                action="provider.ownership.transferred",
                actor=self.owner,
            ).exists()
        )
