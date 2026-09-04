from django.contrib.auth import get_user_model
from django.test import TestCase

from palvelut.apps.discovery.models import PublicProviderDocument
from palvelut.apps.discovery.services import refresh_public_provider_document
from palvelut.apps.moderation.services import moderate_provider
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision


class ApprovedPublicDocumentTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="discovery-staff",
            password=None,
            is_staff=True,
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Approved Oy",
            display_name="Mutable provider row",
            claim_status=Provider.ClaimStatus.APPROVED,
            lifecycle=Provider.Lifecycle.PUBLISHED,
        )
        self.approved = ProfileRevision.objects.create(
            provider=self.provider,
            status=ProfileRevision.Status.APPROVED,
            payload={
                "display_name": "Approved Name",
                "summary": "Hyvä PALVELU",
                "locales": {"ru": "Одобрено"},
            },
            created_by=self.staff,
        )

    def test_document_uses_only_approved_revision_payload(self) -> None:
        pending = ProfileRevision.objects.create(
            provider=self.provider,
            status=ProfileRevision.Status.PENDING,
            payload={"display_name": "Pending Secret"},
            created_by=self.staff,
        )

        document = refresh_public_provider_document(provider_id=self.provider.pk)

        self.assertIsNotNone(document)
        assert document is not None
        self.assertEqual(document.revision_id, self.approved.pk)
        self.assertEqual(document.payload, self.approved.payload)
        self.assertIn("approved name", document.search_text)
        self.assertIn("hyvä palvelu", document.search_text)
        self.assertNotIn("pending secret", document.search_text)
        self.assertNotEqual(document.revision_id, pending.pk)

    def test_non_public_state_removes_existing_document(self) -> None:
        refresh_public_provider_document(provider_id=self.provider.pk)
        self.assertTrue(
            PublicProviderDocument.objects.filter(provider=self.provider).exists()
        )

        self.provider.lifecycle = Provider.Lifecycle.SUSPENDED
        self.provider.save(update_fields=("lifecycle", "updated_at"))
        result = refresh_public_provider_document(provider_id=self.provider.pk)

        self.assertIsNone(result)
        self.assertFalse(
            PublicProviderDocument.objects.filter(provider=self.provider).exists()
        )

    def test_missing_approved_revision_never_creates_public_document(self) -> None:
        self.approved.delete()
        ProfileRevision.objects.create(
            provider=self.provider,
            status=ProfileRevision.Status.PENDING,
            payload={"display_name": "Pending Only"},
            created_by=self.staff,
        )

        result = refresh_public_provider_document(provider_id=self.provider.pk)

        self.assertIsNone(result)
        self.assertFalse(
            PublicProviderDocument.objects.filter(provider=self.provider).exists()
        )

    def test_moderation_publish_builds_and_suspend_removes_document(self) -> None:
        self.approved.status = ProfileRevision.Status.SUPERSEDED
        self.approved.save(update_fields=("status",))
        self.provider.lifecycle = Provider.Lifecycle.PENDING
        self.provider.save(update_fields=("lifecycle", "updated_at"))
        candidate = ProfileRevision.objects.create(
            provider=self.provider,
            status=ProfileRevision.Status.PENDING,
            payload={"display_name": "Published Candidate"},
            created_by=self.staff,
        )

        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )

        document = PublicProviderDocument.objects.get(provider=self.provider)
        self.assertEqual(document.revision_id, candidate.pk)
        self.assertEqual(document.payload["display_name"], "Published Candidate")

        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="suspend",
        )
        self.assertFalse(
            PublicProviderDocument.objects.filter(provider=self.provider).exists()
        )
