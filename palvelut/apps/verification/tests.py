from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from palvelut.apps.providers.models import Provider
from palvelut.apps.verification.models import VerificationCheck, VerificationEvent
from palvelut.apps.verification.services import change_verification_status


class VerificationAuditTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="verification-staff",
            password="not-used",  # test-only
            is_staff=True,
        )
        self.user = user_model.objects.create_user(
            username="verification-user",
            password="not-used",  # test-only
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Verified Example Oy",
            display_name="Verified Example",
        )
        self.check = VerificationCheck.objects.create(
            provider=self.provider,
            kind="business_registry",
            checked_by=self.staff,
        )

    def test_status_change_records_actor_timestamp_and_transition(self) -> None:
        change_verification_status(
            check_id=self.check.pk,
            actor=self.staff,
            status=VerificationCheck.Status.VERIFIED,
            metadata={"source": "staff-review"},
        )

        self.check.refresh_from_db()
        self.assertEqual(self.check.status, VerificationCheck.Status.VERIFIED)
        event = VerificationEvent.objects.get(check=self.check)
        self.assertEqual(event.actor, self.staff)
        self.assertEqual(event.previous_status, VerificationCheck.Status.PENDING)
        self.assertEqual(event.status, VerificationCheck.Status.VERIFIED)
        self.assertIsNotNone(event.created_at)
        self.assertEqual(event.metadata, {"source": "staff-review"})

    def test_repeated_same_status_does_not_create_duplicate_event(self) -> None:
        change_verification_status(
            check_id=self.check.pk,
            actor=self.staff,
            status=VerificationCheck.Status.PENDING,
        )
        self.assertFalse(VerificationEvent.objects.filter(check=self.check).exists())

    def test_non_staff_cannot_change_verification_status(self) -> None:
        with self.assertRaises(PermissionDenied):
            change_verification_status(
                check_id=self.check.pk,
                actor=self.user,
                status=VerificationCheck.Status.REJECTED,
            )

        self.check.refresh_from_db()
        self.assertEqual(self.check.status, VerificationCheck.Status.PENDING)
        self.assertFalse(VerificationEvent.objects.filter(check=self.check).exists())

    def test_invalid_status_is_rejected_without_event(self) -> None:
        with self.assertRaisesMessage(
            ValidationError,
            "Unsupported verification status",
        ):
            change_verification_status(
                check_id=self.check.pk,
                actor=self.staff,
                status="invalid",
            )

        self.assertFalse(VerificationEvent.objects.filter(check=self.check).exists())
