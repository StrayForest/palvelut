from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings
from django.urls import reverse

from palvelut.apps.moderation.models import AuditEvent, ModerationCase, ModerationEvent
from palvelut.apps.moderation.services import (
    appeal_content_case,
    content_report_status,
    provider_case_timeline,
    staff_update_content_case,
    submit_content_report,
)
from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.publishing.models import ProviderSlug


class ContentReportWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        user_model = get_user_model()
        cls.staff = user_model.objects.create_user(
            username="report-moderator",
            is_staff=True,
        )
        cls.owner = user_model.objects.create_user(username="report-owner")
        cls.other = user_model.objects.create_user(username="report-other")
        cls.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Reported Example Oy",
            display_name="Reported Example",
            claim_status=Provider.ClaimStatus.APPROVED,
        )
        ProviderMembership.objects.create(
            provider=cls.provider,
            account=cls.owner,
            role=ProviderMembership.Role.OWNER,
        )

    def test_anonymous_report_creates_case_without_reporter_identity(self) -> None:
        receipt = submit_content_report(
            provider_id=self.provider.pk,
            category="incorrect_content",
            details="The public address is outdated.",
        )
        case = ModerationCase.objects.get(pk=receipt.case_id)
        self.assertEqual(case.kind, ModerationCase.Kind.CONTENT_REPORT)
        self.assertIsNone(case.opened_by)
        self.assertNotEqual(case.status_token_hash, receipt.status_token)
        self.assertEqual(case.content_report.category, "incorrect_content")
        event = case.events.get(event_type="report.received")
        self.assertIsNone(event.actor)
        self.assertFalse(event.visible_to_provider)
        self.assertEqual(event.metadata, {"category": "incorrect_content"})

    def test_reporter_status_requires_receipt_secret(self) -> None:
        receipt = submit_content_report(
            provider_id=self.provider.pk,
            category="other",
            details="Please review this profile.",
        )
        case = content_report_status(
            case_id=receipt.case_id,
            status_token=receipt.status_token,
        )
        self.assertEqual(case.status, ModerationCase.Status.OPEN)
        with self.assertRaises(PermissionDenied):
            content_report_status(case_id=receipt.case_id, status_token="wrong-token")

    def test_staff_notice_is_provider_visible_and_audited(self) -> None:
        receipt = submit_content_report(
            provider_id=self.provider.pk,
            category="incorrect_content",
            details="Incorrect profile fact.",
        )
        staff_update_content_case(
            case_id=receipt.case_id,
            actor=self.staff,
            action="notice",
            note="Please review and correct the reported fact.",
        )
        case, events = provider_case_timeline(
            case_id=receipt.case_id,
            actor=self.owner,
        )
        self.assertEqual(case.status, ModerationCase.Status.OPEN)
        self.assertEqual([event.event_type for event in events], ["provider.notice"])
        audit_event = AuditEvent.objects.get(
            provider=self.provider,
            actor=self.staff,
            action="content_report.notice",
        )
        self.assertEqual(audit_event.metadata, {"case_id": str(receipt.case_id)})

    def test_provider_can_appeal_and_staff_can_resolve_with_status_trail(self) -> None:
        receipt = submit_content_report(
            provider_id=self.provider.pk,
            category="incorrect_content",
            details="Incorrect profile fact.",
        )
        staff_update_content_case(
            case_id=receipt.case_id,
            actor=self.staff,
            action="notice",
            note="Provider notice.",
        )
        appeal_content_case(
            case_id=receipt.case_id,
            actor=self.owner,
            note="The current information is correct.",
        )
        staff_update_content_case(
            case_id=receipt.case_id,
            actor=self.staff,
            action="resolve",
            note="Reviewed provider appeal and resolved the case.",
        )
        case, events = provider_case_timeline(
            case_id=receipt.case_id,
            actor=self.owner,
        )
        self.assertEqual(case.status, ModerationCase.Status.RESOLVED)
        self.assertIsNotNone(case.closed_at)
        self.assertEqual(
            [event.event_type for event in events],
            ["provider.notice", "provider.appeal", "case.resolved"],
        )

    def test_non_member_cannot_read_or_appeal_provider_case(self) -> None:
        receipt = submit_content_report(
            provider_id=self.provider.pk,
            category="other",
            details="Review requested.",
        )
        with self.assertRaises(PermissionDenied):
            provider_case_timeline(case_id=receipt.case_id, actor=self.other)
        with self.assertRaises(PermissionDenied):
            appeal_content_case(
                case_id=receipt.case_id,
                actor=self.other,
                note="Unauthorized appeal.",
            )
        self.assertFalse(
            ModerationEvent.objects.filter(
                case_id=receipt.case_id,
                event_type="provider.appeal",
            ).exists()
        )


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "content-report-rate-limit-tests",
        }
    }
)
class ContentReportPublicViewTests(TestCase):
    def setUp(self) -> None:
        cache.clear()
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Public Report Oy",
            display_name="Public Report",
            claim_status=Provider.ClaimStatus.APPROVED,
            lifecycle=Provider.Lifecycle.PUBLISHED,
        )
        self.slug = ProviderSlug.objects.create(
            provider=self.provider,
            slug="public-report",
        )

    def test_anonymous_reports_are_acknowledged_and_rate_limited(self) -> None:
        url = reverse(
            "content-report-provider",
            kwargs={"locale": "en", "slug": self.slug.slug},
        )
        self.assertEqual(self.client.get(url).status_code, 200)
        for index in range(5):
            response = self.client.post(
                url,
                {"category": "other", "details": f"Report {index}"},
                REMOTE_ADDR="203.0.113.15",
            )
            self.assertEqual(response.status_code, 202)
        limited = self.client.post(
            url,
            {"category": "other", "details": "Report 6"},
            REMOTE_ADDR="203.0.113.15",
        )
        self.assertEqual(limited.status_code, 429)
        self.assertEqual(limited["Retry-After"], "3600")
        self.assertEqual(ModerationCase.objects.count(), 5)

    def test_report_route_is_not_available_for_non_published_provider(self) -> None:
        self.provider.lifecycle = Provider.Lifecycle.SUSPENDED
        self.provider.save(update_fields=("lifecycle", "updated_at"))
        url = reverse(
            "content-report-provider",
            kwargs={"locale": "en", "slug": self.slug.slug},
        )
        self.assertEqual(self.client.get(url).status_code, 404)
