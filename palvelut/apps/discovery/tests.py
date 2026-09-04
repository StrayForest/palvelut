from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.discovery.services import rebuild_provider_read_document
from palvelut.apps.moderation.services import moderate_provider
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision


class ProviderReadDocumentTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="read-model-moderator",
            password="not-used",  # test-only
            is_staff=True,
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Read Model Oy",
            display_name="Read Model",
            claim_status=Provider.ClaimStatus.APPROVED,
        )

    def _revision(self, payload: dict[str, str]) -> ProfileRevision:
        return ProfileRevision.objects.create(
            provider=self.provider,
            status=ProfileRevision.Status.PENDING,
            payload=payload,
            created_by=self.staff,
        )

    def test_approve_builds_document_from_exact_approved_revision(self) -> None:
        revision = self._revision(
            {"display_name": "Approved name", "summary": "Approved"}
        )

        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )

        document = ProviderReadDocument.objects.get(provider=self.provider)
        revision.refresh_from_db()
        self.assertEqual(revision.status, ProfileRevision.Status.APPROVED)
        self.assertEqual(document.source_revision, revision)
        self.assertEqual(document.document, revision.payload)

    def test_pending_edit_does_not_leak_into_existing_document(self) -> None:
        approved = self._revision({"display_name": "Live name"})
        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )
        pending = self._revision({"display_name": "Pending name"})

        document = ProviderReadDocument.objects.get(provider=self.provider)
        self.assertEqual(document.source_revision, approved)
        self.assertEqual(document.document["display_name"], "Live name")
        self.assertNotEqual(document.source_revision, pending)

    def test_rebuild_refuses_provider_without_approved_revision(self) -> None:
        self.provider.lifecycle = Provider.Lifecycle.PUBLISHED
        self.provider.save(update_fields=("lifecycle", "updated_at"))
        self._revision({"display_name": "Pending only"})

        with self.assertRaisesMessage(
            ValidationError,
            "Public read document requires an approved revision",
        ):
            rebuild_provider_read_document(provider_id=self.provider.pk)

        self.assertFalse(
            ProviderReadDocument.objects.filter(provider=self.provider).exists()
        )

    def test_suspend_removes_public_document(self) -> None:
        self._revision({"display_name": "Published"})
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

    def test_rebuild_existing_document_stays_within_query_budget(self) -> None:
        self._revision({"display_name": "Published"})
        moderate_provider(
            provider_id=self.provider.pk,
            actor=self.staff,
            action="approve",
        )

        with CaptureQueriesContext(connection) as queries:
            rebuild_provider_read_document(provider_id=self.provider.pk)

        self.assertLessEqual(
            len(queries),
            8,
            "Provider read-document rebuild exceeded the P1 database query budget",
        )
