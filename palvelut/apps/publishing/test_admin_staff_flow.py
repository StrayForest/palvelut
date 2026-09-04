from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.moderation.services import moderate_provider
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.admin import ProfileRevisionAdmin
from palvelut.apps.publishing.models import ProfileRevision


class StaffProfileRevisionAdminFlowTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_superuser(
            username="staff-publisher",
            email="staff-publisher@example.invalid",
            password="not-used",  # test-only
        )
        self.factory = RequestFactory()
        self.model_admin = ProfileRevisionAdmin(ProfileRevision, admin.site)

    def _request(self):
        request = self.factory.post("/admin/publishing/profilerevision/add/")
        request.user = self.staff
        return request

    def test_staff_can_create_reviewable_revision_without_manual_code(self) -> None:
        provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Owner Confirmed Oy",
            display_name="Owner Confirmed",
            y_tunnus="1234567-1",
            claim_status=Provider.ClaimStatus.APPROVED,
            claim_evidence={"method": "staff_owner_confirmation"},
        )
        request = self._request()

        self.assertTrue(self.model_admin.has_add_permission(request))
        readonly = self.model_admin.get_readonly_fields(request, obj=None)
        self.assertNotIn("provider", readonly)
        self.assertNotIn("payload", readonly)

        revision = ProfileRevision(
            provider=provider,
            payload={"display_name": "Owner Confirmed"},
        )
        self.model_admin.save_model(request, revision, form=None, change=False)

        revision.refresh_from_db()
        self.assertEqual(revision.status, ProfileRevision.Status.PENDING)
        self.assertEqual(revision.created_by, self.staff)

        moderate_provider(
            provider_id=provider.pk,
            actor=self.staff,
            action="approve",
        )

        provider.refresh_from_db()
        revision.refresh_from_db()
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.PUBLISHED)
        self.assertEqual(revision.status, ProfileRevision.Status.APPROVED)
        document = ProviderReadDocument.objects.get(provider=provider)
        self.assertEqual(document.source_revision, revision)
        self.assertEqual(document.document, revision.payload)
