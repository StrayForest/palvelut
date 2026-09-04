from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from palvelut.apps.providers.models import Provider

from .models import VerificationCheck, VerificationEvent
from .services import change_verification_status


class VerificationAuditHistoryTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(
            username="verification-staff",
            is_staff=True,
        )
        self.user = user_model.objects.create_user(username="verification-user")
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Verification Example Oy",
            display_name="Verification Example",
        )
        self.check = VerificationCheck.objects.create(
            provider=self.provider,
            kind="business_identity",
            checked_by=self.staff,
        )

    def test_status_change_records_actor_timestamp_and_status(self) -> None:
        change_verification_status(
            check_id=self.check.pk,
            actor=self.staff,
            status=VerificationCheck.Status.VERIFIED,
            metadata={"reference": "synthetic"},
        )

        self.check.refresh_from_db()
        event = VerificationEvent.objects.get(check=self.check)
        self.assertEqual(self.check.status, VerificationCheck.Status.VERIFIED)
        self.assertEqual(event.status, VerificationCheck.Status.VERIFIED)
        self.assertEqual(event.actor, self.staff)
        self.assertIsNotNone(event.created_at)
        self.assertEqual(event.metadata["reference"], "synthetic")

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
