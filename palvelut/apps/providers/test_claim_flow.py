from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from palvelut.apps.moderation.models import AuditEvent

from .claim_services import resolve_provider_claim, submit_provider_claim
from .models import Provider, ProviderMembership


class ProviderClaimFlowTests(TestCase):
    def setUp(self) -> None:
        self.claimant = get_user_model().objects.create_user(
            username="claimant@example.com",
            email="claimant@example.com",
            password="Strong-passphrase-2026!",
        )
        self.other = get_user_model().objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="Strong-passphrase-2026!",
        )
        self.staff = get_user_model().objects.create_user(
            username="staff-claim@example.com",
            email="staff-claim@example.com",
            password="Strong-passphrase-2026!",
            is_staff=True,
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.UNCLAIMED,
            claim_status=Provider.ClaimStatus.UNCLAIMED,
            legal_name="Claimable Oy",
            display_name="Claimable",
            y_tunnus="7654321-0",
        )

    def _submit(self) -> None:
        submit_provider_claim(
            provider_id=self.provider.pk,
            actor=self.claimant,
            evidence_kind="registry_signatory",
            evidence_reference="PRH signatory record 2026-09-05",
        )

    def test_claim_submission_requires_independent_business_control_evidence(self) -> None:
        self.client.force_login(self.claimant)
        response = self.client.post(
            reverse("account-claim-provider", kwargs={"provider_id": self.provider.pk}),
            {"evidence_kind": "email", "evidence_reference": self.claimant.email},
        )
        self.assertEqual(response.status_code, 200)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.claim_status, Provider.ClaimStatus.UNCLAIMED)
        self.assertFalse(ProviderMembership.objects.filter(provider=self.provider).exists())

        response = self.client.post(
            reverse("account-claim-provider", kwargs={"provider_id": self.provider.pk}),
            {
                "evidence_kind": "business_domain_email",
                "evidence_reference": "owner@claimable.example",
            },
        )
        self.assertRedirects(response, reverse("account-claim-list"))
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.claim_status, Provider.ClaimStatus.PENDING)
        self.assertEqual(self.provider.lifecycle, Provider.Lifecycle.UNCLAIMED)
        self.assertEqual(
            self.provider.claim_evidence["claimant_user_id"], str(self.claimant.pk)
        )
        self.assertFalse(ProviderMembership.objects.filter(provider=self.provider).exists())
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=self.provider,
                actor=self.claimant,
                action="provider.claim_submitted",
            ).exists()
        )

    def test_competing_claim_cannot_replace_pending_claim(self) -> None:
        self._submit()
        with self.assertRaises(ValidationError):
            submit_provider_claim(
                provider_id=self.provider.pk,
                actor=self.other,
                evidence_kind="staff_reviewed_equivalent",
                evidence_reference="separate documents",
            )
        self.provider.refresh_from_db()
        self.assertEqual(
            self.provider.claim_evidence["claimant_user_id"], str(self.claimant.pk)
        )

    def test_staff_approval_atomically_grants_owner_but_keeps_profile_unpublished(self) -> None:
        self._submit()
        resolve_provider_claim(
            provider_id=self.provider.pk,
            actor=self.staff,
            decision="approve",
            review_note="Registry signatory matches legal identity.",
        )
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.claim_status, Provider.ClaimStatus.APPROVED)
        self.assertEqual(self.provider.lifecycle, Provider.Lifecycle.DRAFT)
        membership = ProviderMembership.objects.get(provider=self.provider)
        self.assertEqual(membership.account, self.claimant)
        self.assertEqual(membership.role, ProviderMembership.Role.OWNER)
        self.assertEqual(self.provider.claim_evidence["decision"], "approve")
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=self.provider,
                actor=self.staff,
                action="provider.claim_approved",
            ).exists()
        )

    def test_staff_rejection_keeps_provider_unclaimed_without_membership(self) -> None:
        self._submit()
        resolve_provider_claim(
            provider_id=self.provider.pk,
            actor=self.staff,
            decision="reject",
            review_note="Evidence does not establish control.",
        )
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.claim_status, Provider.ClaimStatus.REJECTED)
        self.assertEqual(self.provider.lifecycle, Provider.Lifecycle.UNCLAIMED)
        self.assertFalse(ProviderMembership.objects.filter(provider=self.provider).exists())
        self.assertEqual(self.provider.claim_evidence["decision"], "reject")

    def test_non_staff_cannot_open_staff_claim_review(self) -> None:
        self._submit()
        self.client.force_login(self.claimant)
        response = self.client.get(
            reverse("staff-claim-review", kwargs={"provider_id": self.provider.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_staff_claim_review_route_requires_mfa_session_and_can_approve(self) -> None:
        self._submit()
        self.client.force_login(self.staff)
        response = self.client.get(reverse("staff-claim-list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("staff-mfa"), response.url)

        session = self.client.session
        session["staff_mfa_verified"] = True
        session.save()
        response = self.client.post(
            reverse("staff-claim-review", kwargs={"provider_id": self.provider.pk}),
            {"decision": "approve", "review_note": "Control confirmed."},
        )
        self.assertRedirects(response, reverse("staff-claim-list"))
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.lifecycle, Provider.Lifecycle.DRAFT)
        self.assertTrue(
            ProviderMembership.objects.filter(
                provider=self.provider,
                account=self.claimant,
                role=ProviderMembership.Role.OWNER,
            ).exists()
        )
