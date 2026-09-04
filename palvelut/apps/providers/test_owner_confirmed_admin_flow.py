from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.publishing.models import ProfileRevision


class OwnerConfirmedStaffPublishTests(TestCase):
    def setUp(self) -> None:
        self.staff = get_user_model().objects.create_superuser(
            username="owner-flow-staff",
            email="owner-flow-staff@example.invalid",
            password="test-only-password",
        )
        self.owner = get_user_model().objects.create_user(
            username="owner-flow-owner",
            password="test-only-password",
        )
        self.client.force_login(self.staff)

    def test_staff_can_create_owner_confirmed_provider_and_publish_it(self) -> None:
        add_url = reverse("admin:providers_provider_add")
        add_page = self.client.get(add_url)
        self.assertEqual(add_page.status_code, 200)

        post_data = {
            "provider_type": Provider.Type.BUSINESS,
            "claim_status": Provider.ClaimStatus.APPROVED,
            "claim_evidence": '{"kind":"staff_review","reference":"owner-confirmed"}',
            "legal_name": "Owner Confirmed Oy",
            "display_name": "Owner Confirmed",
            "y_tunnus": "7654321-0",
            "_save": "Save",
        }

        inline_admin_formsets = add_page.context["inline_admin_formsets"]
        for inline_admin_formset in inline_admin_formsets:
            formset = inline_admin_formset.formset
            prefix = formset.prefix
            is_membership = formset.model is ProviderMembership
            post_data[f"{prefix}-TOTAL_FORMS"] = "1" if is_membership else "0"
            post_data[f"{prefix}-INITIAL_FORMS"] = "0"
            post_data[f"{prefix}-MIN_NUM_FORMS"] = "0"
            post_data[f"{prefix}-MAX_NUM_FORMS"] = "1000"
            if is_membership:
                post_data[f"{prefix}-0-account"] = str(self.owner.pk)
                post_data[f"{prefix}-0-role"] = ProviderMembership.Role.OWNER
                post_data[f"{prefix}-0-is_active"] = "on"

        create_response = self.client.post(add_url, post_data)
        self.assertEqual(create_response.status_code, 302)

        provider = Provider.objects.get(y_tunnus="7654321-0")
        membership = ProviderMembership.objects.get(provider=provider)
        revision = ProfileRevision.objects.get(provider=provider)

        self.assertEqual(provider.claim_status, Provider.ClaimStatus.APPROVED)
        self.assertEqual(membership.account, self.owner)
        self.assertEqual(membership.role, ProviderMembership.Role.OWNER)
        self.assertEqual(revision.status, ProfileRevision.Status.DRAFT)
        self.assertEqual(revision.created_by, self.staff)
        self.assertEqual(revision.payload["display_name"], "Owner Confirmed")

        publish_response = self.client.post(
            reverse("admin:providers_provider_changelist"),
            {
                "action": "approve_selected",
                "_selected_action": [str(provider.pk)],
                "select_across": "0",
            },
        )
        self.assertEqual(publish_response.status_code, 302)

        provider.refresh_from_db()
        revision.refresh_from_db()
        document = ProviderReadDocument.objects.get(provider=provider)

        self.assertEqual(provider.lifecycle, Provider.Lifecycle.PUBLISHED)
        self.assertEqual(revision.status, ProfileRevision.Status.APPROVED)
        self.assertEqual(document.source_revision, revision)
        self.assertEqual(document.document, revision.payload)
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=provider,
                actor=self.staff,
                action="provider.created",
            ).exists()
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=provider,
                actor=self.staff,
                action="provider.approved",
            ).exists()
        )
