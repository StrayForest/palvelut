from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from palvelut.apps.moderation.models import AuditEvent

from .claim_services import resolve_provider_claim
from .models import Provider, ProviderMembership

TEST_PASSWORD = "Strong-passphrase-2026!"  # test-only


class ProviderSelfStartFlowTests(TestCase):
    def setUp(self) -> None:
        self.provider_user = get_user_model().objects.create_user(
            username="fresh-provider@example.com",
            email="fresh-provider@example.com",
            password=TEST_PASSWORD,
            is_active=True,
        )
        self.staff = get_user_model().objects.create_user(
            username="self-start-staff@example.com",
            email="self-start-staff@example.com",
            password=TEST_PASSWORD,
            is_staff=True,
        )

    def _start_business_claim(self):
        self.client.force_login(self.provider_user)
        return self.client.post(
            reverse("account-provider-start"),
            {
                "provider_type": Provider.Type.BUSINESS,
                "legal_name": "Fresh Provider Oy",
                "display_name": "Fresh Provider",
                "y_tunnus": "2468135-7",
                "evidence_kind": "registry_signatory",
                "evidence_reference": "PRH signatory record for Fresh Provider Oy",
            },
        )

    def test_public_provider_entry_replaces_disabled_beta_message(self) -> None:
        home = self.client.get(reverse("localized-home", kwargs={"locale": "en"}))
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, reverse("for-professionals", kwargs={"locale": "en"}))
        self.assertNotContains(home, "Provider self-service is being prepared")

        entry = self.client.get(
            reverse("for-professionals", kwargs={"locale": "en"})
        )
        self.assertEqual(entry.status_code, 200)
        self.assertContains(entry, reverse("account-register"))
        self.assertContains(entry, reverse("account-login"))

    def test_new_verified_account_can_start_private_provider_without_preseed(
        self,
    ) -> None:
        self.assertFalse(Provider.objects.exists())
        self.assertFalse(ProviderMembership.objects.exists())

        response = self._start_business_claim()
        self.assertRedirects(response, reverse("provider-workspace"))

        provider = Provider.objects.get(y_tunnus="2468135-7")
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.UNCLAIMED)
        self.assertEqual(provider.claim_status, Provider.ClaimStatus.PENDING)
        self.assertEqual(
            provider.claim_evidence["claimant_user_id"], str(self.provider_user.pk)
        )
        self.assertFalse(
            ProviderMembership.objects.filter(provider=provider).exists()
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=provider,
                actor=self.provider_user,
                action="provider.claim_submitted",
            ).exists()
        )

        workspace = self.client.get(reverse("provider-workspace"))
        self.assertEqual(workspace.status_code, 200)
        self.assertContains(workspace, "Fresh Provider")
        self.assertContains(workspace, "Ownership claim:")
        self.assertContains(workspace, "Pending")
        self.assertContains(workspace, "Nothing is public yet")

    def test_business_self_start_requires_y_tunnus(self) -> None:
        self.client.force_login(self.provider_user)
        response = self.client.post(
            reverse("account-provider-start"),
            {
                "provider_type": Provider.Type.BUSINESS,
                "legal_name": "Missing Id Oy",
                "display_name": "Missing Id",
                "y_tunnus": "",
                "evidence_kind": "registry_signatory",
                "evidence_reference": "registry evidence",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Y-tunnus is required for a business provider")
        self.assertFalse(Provider.objects.exists())

    def test_existing_y_tunnus_directs_provider_to_claim_existing_record(self) -> None:
        Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.UNCLAIMED,
            claim_status=Provider.ClaimStatus.UNCLAIMED,
            legal_name="Existing Oy",
            display_name="Existing",
            y_tunnus="2468135-7",
        )
        self.client.force_login(self.provider_user)
        response = self.client.post(
            reverse("account-provider-start"),
            {
                "provider_type": Provider.Type.BUSINESS,
                "legal_name": "Duplicate Oy",
                "display_name": "Duplicate",
                "y_tunnus": "2468135-7",
                "evidence_kind": "registry_signatory",
                "evidence_reference": "registry evidence",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Claim the existing profile instead")
        self.assertEqual(Provider.objects.count(), 1)

    def test_staff_approval_unlocks_workspace_without_publishing_profile(self) -> None:
        self._start_business_claim()
        provider = Provider.objects.get(y_tunnus="2468135-7")

        resolve_provider_claim(
            provider_id=provider.pk,
            actor=self.staff,
            decision="approve",
            review_note="Control evidence matches legal identity.",
        )
        provider.refresh_from_db()
        self.assertEqual(provider.claim_status, Provider.ClaimStatus.APPROVED)
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.DRAFT)
        self.assertTrue(
            ProviderMembership.objects.filter(
                provider=provider,
                account=self.provider_user,
                role=ProviderMembership.Role.OWNER,
                is_active=True,
            ).exists()
        )

        workspace = self.client.get(reverse("provider-workspace"))
        self.assertContains(workspace, "Edit profile")
        self.assertNotContains(workspace, "Ownership claim: Pending")

    def test_provider_login_redirects_to_workspace(self) -> None:
        response = self.client.post(
            reverse("account-login"),
            {"username": self.provider_user.email, "password": TEST_PASSWORD},
        )
        self.assertRedirects(response, reverse("provider-workspace"))
