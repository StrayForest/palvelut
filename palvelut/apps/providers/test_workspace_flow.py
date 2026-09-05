from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.providers.workspace_services import (
    autosave_revision,
    submit_revision,
)
from palvelut.apps.publishing.models import ProfileRevision
from palvelut.apps.publishing.workflow import approve_revision, request_revision_changes


class ProviderWorkspaceFlowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="owner@example.test",
            email="owner@example.test",
            password="test-only-pass",
        )
        self.staff = user_model.objects.create_user(
            username="staff@example.test",
            email="staff@example.test",
            password="test-only-pass",
            is_staff=True,
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.DRAFT,
            claim_status=Provider.ClaimStatus.APPROVED,
            legal_name="Old Legal Oy",
            display_name="Old Display",
            y_tunnus="1234567-8",
        )
        ProviderMembership.objects.create(
            provider=self.provider,
            account=self.owner,
            role=ProviderMembership.Role.OWNER,
        )

    def test_draft_autosave_preview_submit_and_approve(self):
        revision = autosave_revision(
            provider_id=self.provider.pk,
            account=self.owner,
            payload={
                "provider_type": "business",
                "legal_name": "New Legal Oy",
                "display_name": "New Display",
                "y_tunnus": "1234567-8",
            },
        )
        self.assertEqual(revision.status, ProfileRevision.Status.DRAFT)
        submitted = submit_revision(provider_id=self.provider.pk, account=self.owner)
        self.assertEqual(submitted.status, ProfileRevision.Status.PENDING)
        approve_revision(revision_id=submitted.pk, actor=self.staff)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.display_name, "New Display")
        self.assertEqual(self.provider.lifecycle, Provider.Lifecycle.PUBLISHED)

    def test_live_profile_remains_visible_while_revision_is_pending_or_corrected(self):
        self.provider.lifecycle = Provider.Lifecycle.PUBLISHED
        self.provider.save(update_fields=("lifecycle",))
        autosave_revision(
            provider_id=self.provider.pk,
            account=self.owner,
            payload={
                "provider_type": "business",
                "legal_name": "Pending Legal Oy",
                "display_name": "Pending Display",
                "y_tunnus": "1234567-8",
            },
        )
        revision = submit_revision(provider_id=self.provider.pk, account=self.owner)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.lifecycle, Provider.Lifecycle.PUBLISHED)
        self.assertEqual(self.provider.display_name, "Old Display")
        request_revision_changes(
            revision_id=revision.pk,
            actor=self.staff,
            note="Fix name",
        )
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.lifecycle, Provider.Lifecycle.PUBLISHED)
        self.assertEqual(self.provider.display_name, "Old Display")

    def test_other_account_cannot_open_workspace_provider(self):
        other = get_user_model().objects.create_user(
            username="other@example.test",
            password="test-only-pass",
        )
        self.client.force_login(other)
        response = self.client.get(
            reverse("provider-workspace-edit", args=[self.provider.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_provider_write_rejects_missing_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.owner)
        response = csrf_client.post(
            reverse("provider-workspace-edit", args=[self.provider.pk]),
            {
                "provider_type": "business",
                "legal_name": "CSRF Legal Oy",
                "display_name": "CSRF Display",
                "y_tunnus": "1234567-8",
            },
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(ProfileRevision.objects.filter(provider=self.provider).exists())

    def test_owner_can_preview_and_submit_through_http(self):
        self.client.force_login(self.owner)
        edit_url = reverse("provider-workspace-edit", args=[self.provider.pk])
        response = self.client.post(
            edit_url,
            {
                "provider_type": "business",
                "legal_name": "HTTP Legal Oy",
                "display_name": "HTTP Display",
                "y_tunnus": "1234567-8",
            },
        )
        self.assertEqual(response.status_code, 302)
        preview = self.client.get(
            reverse("provider-workspace-preview", args=[self.provider.pk])
        )
        self.assertContains(preview, "HTTP Display")
        submitted = self.client.post(
            reverse("provider-workspace-submit", args=[self.provider.pk])
        )
        self.assertEqual(submitted.status_code, 302)
        self.assertTrue(
            ProfileRevision.objects.filter(
                provider=self.provider,
                status=ProfileRevision.Status.PENDING,
            ).exists()
        )
