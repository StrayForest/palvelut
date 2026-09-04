from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.test import TestCase

from palvelut.apps.moderation.models import ModerationCase, ModerationEvent
from palvelut.apps.moderation.services import close_moderation_case
from palvelut.apps.providers.models import Provider
from palvelut.apps.verification.models import VerificationCheck


class ModerationActorTimestampTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="case-moderator",
            password="not-used",  # test-only
            is_staff=True,
        )
        self.user = user_model.objects.create_user(
            username="case-user",
            password="not-used",  # test-only
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Audit Example Oy",
            display_name="Audit Example",
        )

    def _case(self) -> ModerationCase:
        return ModerationCase.objects.create(
            provider=self.provider,
            reason="identity_review",
            opened_by=self.staff,
        )

    def test_case_closure_records_actor_timestamp_and_event(self) -> None:
        case = self._case()

        close_moderation_case(
            case_id=case.pk,
            actor=self.staff,
            resolution="resolved",
            note="Identity confirmed",
        )

        case.refresh_from_db()
        self.assertEqual(case.status, ModerationCase.Status.RESOLVED)
        self.assertEqual(case.closed_by, self.staff)
        self.assertIsNotNone(case.closed_at)
        event = ModerationEvent.objects.get(case=case, event_type="case.resolved")
        self.assertEqual(event.actor, self.staff)
        self.assertIsNotNone(event.created_at)
        self.assertEqual(event.note, "Identity confirmed")

    def test_database_rejects_closed_case_without_actor_and_timestamp(self) -> None:
        case = self._case()

        with self.assertRaises(IntegrityError), transaction.atomic():
            ModerationCase.objects.filter(pk=case.pk).update(
                status=ModerationCase.Status.DISMISSED
            )

    def test_non_staff_cannot_close_case(self) -> None:
        case = self._case()

        with self.assertRaises(PermissionDenied):
            close_moderation_case(
                case_id=case.pk,
                actor=self.user,
                resolution="dismissed",
            )

    def test_verification_check_records_actor_and_timestamp(self) -> None:
        check = VerificationCheck.objects.create(
            provider=self.provider,
            kind="business_identity",
            status=VerificationCheck.Status.VERIFIED,
            checked_by=self.staff,
            evidence_metadata={"source": "staff_review"},
        )

        self.assertEqual(check.checked_by, self.staff)
        self.assertIsNotNone(check.checked_at)
