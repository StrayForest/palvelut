from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.discovery.services import publish_approved_revision
from palvelut.apps.moderation.services import moderate_provider
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision


class ApprovedReadDocumentTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="publisher",
            password="not-used",
            is_staff=True,
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Example Oy",
            display_name="Working copy name",
            claim_status=Provider.ClaimStatus.APPROVED,
        )

    def _revision(self, *, status: str, payload: dict[str, object]) -> ProfileRevision:
        return ProfileRevision.objects.create(
            provider=self.provider,
            status=status,
            payload=payload,
            created_by=self.staff,
            reviewed_at=(
                timezone.now()
                if status == ProfileRevision.Status.APPROVED
                else None
            ),
        )

    def test_pending_revision_cannot_generate_public_document(self) -> None:
        revision = self._revision(
            status=ProfileRevision.Status.PENDING,
            payload={"display_name": "Pending secret"},
        )

        with self.assertRaisesMessage(
            ValidationError,
            "Public read documents require an approved revision",
        ):
            publish_approved_revision(revision=revision)

        self.assertFalse(ProviderReadDocument.objects.exists())

    def test_approval_generates_snapshot_from_approved_payload_only(self) -> None:
        revision = self._revision(
            status=ProfileRevision.Status.PENDING,
            payload={
                "display_name": "Published name",
                "description": "Approved description",
                "tags": ["massage", "helsinki"],
            },
        )

        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )

        document = ProviderReadDocument.objects.get(provider=self.provider)
        self.assertEqual(document.source_revision, revision)
        self.assertEqual(document.document, revision.payload)
        self.assertNotIn("Working copy name", document.searchable_text)
        self.assertIn("Published name", document.searchable_text)
        self.assertIn("Approved description", document.searchable_text)

    def test_pending_edit_does_not_replace_existing_public_document(self) -> None:
        approved = self._revision(
            status=ProfileRevision.Status.PENDING,
            payload={"display_name": "Live name"},
        )
        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )
        self._revision(
            status=ProfileRevision.Status.PENDING,
            payload={"display_name": "Pending replacement"},
        )

        document = ProviderReadDocument.objects.get(provider=self.provider)
        self.assertEqual(document.source_revision, approved)
        self.assertEqual(document.document["display_name"], "Live name")

    def test_suspend_removes_public_document(self) -> None:
        self._revision(
            status=ProfileRevision.Status.PENDING,
            payload={"display_name": "Live name"},
        )
        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )
        self.assertTrue(
            ProviderReadDocument.objects.filter(provider=self.provider).exists()
        )

        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="suspend",
        )

        self.assertFalse(
            ProviderReadDocument.objects.filter(provider=self.provider).exists()
        )
