from django.contrib.auth import get_user_model
from django.test import TestCase

from palvelut.apps.discovery.models import PublicProviderDocument
from palvelut.apps.discovery.services import sync_public_provider_document
from palvelut.apps.moderation.services import moderate_provider
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision


class PublicProviderDocumentTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="discovery-moderator",
            password="not-used",  # test-only
            is_staff=True,
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Public Example Oy",
            display_name="Public Example",
            claim_status=Provider.ClaimStatus.APPROVED,
        )

    def _revision(self, payload: dict[str, object]) -> ProfileRevision:
        return ProfileRevision.objects.create(
            provider=self.provider,
            status=ProfileRevision.Status.PENDING,
            payload=payload,
            created_by=self.staff,
        )

    def test_approve_generates_document_from_approved_revision(self) -> None:
        revision = self._revision({"display_name": "Approved name", "marker": "v1"})

        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )

        document = PublicProviderDocument.objects.get(provider=self.provider)
        self.assertEqual(document.revision_id, revision.pk)
        self.assertEqual(document.payload["marker"], "v1")

    def test_pending_edit_does_not_replace_live_document(self) -> None:
        first = self._revision({"marker": "approved"})
        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )
        pending = self._revision({"marker": "pending"})

        sync_public_provider_document(provider_id=self.provider.pk)

        document = PublicProviderDocument.objects.get(provider=self.provider)
        self.assertEqual(document.revision_id, first.pk)
        self.assertNotEqual(document.revision_id, pending.pk)
        self.assertEqual(document.payload["marker"], "approved")

    def test_suspend_removes_public_document(self) -> None:
        self._revision({"marker": "approved"})
        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )
        self.assertTrue(
            PublicProviderDocument.objects.filter(provider=self.provider).exists()
        )

        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="suspend",
        )

        self.assertFalse(
            PublicProviderDocument.objects.filter(provider=self.provider).exists()
        )

    def test_unpublished_provider_cannot_keep_public_document(self) -> None:
        revision = ProfileRevision.objects.create(
            provider=self.provider,
            status=ProfileRevision.Status.APPROVED,
            payload={"marker": "stale"},
            created_by=self.staff,
        )
        PublicProviderDocument.objects.create(
            provider=self.provider,
            revision=revision,
            payload=revision.payload,
        )

        result = sync_public_provider_document(provider_id=self.provider.pk)

        self.assertIsNone(result)
        self.assertFalse(
            PublicProviderDocument.objects.filter(provider=self.provider).exists()
        )
