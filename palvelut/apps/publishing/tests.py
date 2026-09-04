from django.contrib.auth import get_user_model
from django.test import TestCase

from palvelut.apps.moderation.services import moderate_provider
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision, PublicProviderDocument


class PublicProviderDocumentTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="publisher",
            password="not-used",  # test-only
            is_staff=True,
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Read Model Oy",
            display_name="Read Model",
            claim_status=Provider.ClaimStatus.APPROVED,
        )

    def _revision(self, payload: dict[str, object]) -> ProfileRevision:
        return ProfileRevision.objects.create(
            provider=self.provider,
            status=ProfileRevision.Status.PENDING,
            payload=payload,
            created_by=self.staff,
        )

    def test_approval_generates_public_document_from_approved_revision(self) -> None:
        revision = self._revision({"display_name": "Approved name", "city": "Helsinki"})

        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )

        document = PublicProviderDocument.objects.get(provider=self.provider)
        revision.refresh_from_db()
        self.assertEqual(revision.status, ProfileRevision.Status.APPROVED)
        self.assertEqual(document.source_revision, revision)
        self.assertEqual(document.payload, revision.payload)

    def test_pending_revision_does_not_change_live_document(self) -> None:
        first = self._revision({"display_name": "Live name"})
        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )
        first.refresh_from_db()

        pending = self._revision({"display_name": "Pending name"})
        document = PublicProviderDocument.objects.get(provider=self.provider)

        self.assertEqual(document.source_revision, first)
        self.assertEqual(document.payload, {"display_name": "Live name"})
        self.assertEqual(pending.status, ProfileRevision.Status.PENDING)

    def test_next_approval_atomically_replaces_live_document(self) -> None:
        first = self._revision({"display_name": "First"})
        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )
        second = self._revision({"display_name": "Second"})

        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )

        first.refresh_from_db()
        second.refresh_from_db()
        document = PublicProviderDocument.objects.get(provider=self.provider)
        self.assertEqual(first.status, ProfileRevision.Status.SUPERSEDED)
        self.assertEqual(second.status, ProfileRevision.Status.APPROVED)
        self.assertEqual(document.source_revision, second)
        self.assertEqual(document.payload, {"display_name": "Second"})

    def test_suspension_removes_public_document(self) -> None:
        self._revision({"display_name": "Visible"})
        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )

        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="suspend",
        )

        self.assertFalse(
            PublicProviderDocument.objects.filter(provider=self.provider).exists()
        )
