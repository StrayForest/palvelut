import hashlib

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

from palvelut.apps.moderation.models import AuditEvent, ModerationEvent
from palvelut.apps.moderation.services import (
    create_anonymous_report,
    create_provider_notice,
    get_public_report_case,
    staff_update_case,
    submit_appeal,
)
from palvelut.apps.providers.models import Provider, ProviderMembership


class ContentReportWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="owner@example.test",
            password="test-only-password",
        )
        self.outsider = user_model.objects.create_user(
            username="outsider@example.test",
            password="test-only-password",
        )
        self.staff = user_model.objects.create_user(
            username="staff@example.test",
            password="test-only-password",
            is_staff=True,
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.PUBLISHED,
            claim_status=Provider.ClaimStatus.APPROVED,
            legal_name="Report Test Oy",
            display_name="Report Test",
            y_tunnus="1234567-1",
        )
        ProviderMembership.objects.create(
            provider=self.provider,
            account=self.owner,
            role=ProviderMembership.Role.OWNER,
        )

    def test_anonymous_report_uses_private_status_token_without_reporter_identity(self):
        report, token = create_anonymous_report(
            provider=self.provider,
            reason="Incorrect content",
            details="The profile contains information that should be reviewed.",
        )

        self.assertIsNone(report.case.opened_by)
        event = ModerationEvent.objects.get(case=report.case, event_type="report.received")
        self.assertIsNone(event.actor)
        self.assertEqual(report.public_token_hash, hashlib.sha256(token.encode()).hexdigest())
        self.assertNotEqual(report.public_token_hash, token)
        self.assertEqual(get_public_report_case(token=token), report.case)

    def test_staff_notice_and_resolution_are_audited(self):
        report, _token = create_anonymous_report(
            provider=self.provider,
            reason="Incorrect content",
            details="Review this profile.",
        )

        notice = create_provider_notice(
            case_id=report.case_id,
            actor=self.staff,
            message="Please review the reported company details.",
        )
        case = staff_update_case(
            case_id=report.case_id,
            actor=self.staff,
            action="resolve",
            note="Reviewed and resolved.",
        )

        self.assertEqual(notice.case_id, report.case_id)
        self.assertEqual(case.status, case.Status.RESOLVED)
        self.assertTrue(
            AuditEvent.objects.filter(
                provider=self.provider,
                actor=self.staff,
                action="moderation_case.resolved",
            ).exists()
        )
        self.assertEqual(
            list(case.events.values_list("event_type", flat=True)),
            ["report.received", "provider.notice_sent", "case.resolved"],
        )

    def test_provider_member_can_appeal_but_outsider_cannot(self):
        report, _token = create_anonymous_report(
            provider=self.provider,
            reason="Incorrect content",
            details="Review this profile.",
        )
        create_provider_notice(
            case_id=report.case_id,
            actor=self.staff,
            message="Provider notice.",
        )

        appeal = submit_appeal(
            case_id=report.case_id,
            actor=self.owner,
            message="Please reconsider this report.",
        )
        self.assertEqual(appeal.submitted_by, self.owner)

        with self.assertRaises(PermissionDenied):
            submit_appeal(
                case_id=report.case_id,
                actor=self.outsider,
                message="I should not be allowed to appeal.",
            )

    def test_public_and_scoped_surfaces_are_reachable(self):
        response = self.client.post(
            reverse("report-provider", args=("en", self.provider.pk)),
            {"reason": "Incorrect content", "details": "Please review this profile."},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/palvelut/report/", response["Location"])

        report = self.provider.moderation_cases.get().content_report
        self.client.force_login(self.owner)
        provider_response = self.client.get(
            reverse("provider-moderation-case", args=(report.case_id,))
        )
        self.assertEqual(provider_response.status_code, 200)

        self.client.force_login(self.outsider)
        outsider_response = self.client.get(
            reverse("provider-moderation-case", args=(report.case_id,))
        )
        self.assertEqual(outsider_response.status_code, 403)

        self.client.force_login(self.staff)
        staff_response = self.client.get(reverse("staff-moderation-cases"))
        self.assertContains(staff_response, "Incorrect content")
