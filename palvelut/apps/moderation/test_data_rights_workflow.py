from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import DataSubjectRequest, DataSubjectRequestEvent


class LegalTemplateTests(TestCase):
    def test_legal_templates_are_public_drafts_and_noindex(self):
        for document in ("privacy", "terms", "cookies", "accessibility"):
            with self.subTest(document=document):
                response = self.client.get(
                    reverse(
                        "legal-document",
                        kwargs={"locale": "en", "document": document},
                    )
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response,
                    "Draft template — pending owner/legal review before public beta.",
                )
                self.assertContains(response, 'name="robots" content="noindex,follow"')

    def test_unknown_legal_document_is_404(self):
        response = self.client.get(
            reverse(
                "legal-document",
                kwargs={"locale": "en", "document": "unknown"},
            )
        )
        self.assertEqual(response.status_code, 404)


class DataSubjectRequestWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.provider_user = user_model.objects.create_user(
            username="provider@example.test",
            email="provider@example.test",
            password="correct horse battery staple",
        )
        self.staff_user = user_model.objects.create_user(
            username="staff@example.test",
            email="staff@example.test",
            password="correct horse battery staple",
            is_staff=True,
        )

    def test_provider_can_submit_request_and_get_audited_history(self):
        self.client.force_login(self.provider_user)
        response = self.client.post(
            reverse("data-subject-requests"),
            {"kind": "export", "note": "Please provide my account data."},
        )
        self.assertRedirects(response, reverse("data-subject-requests"))

        row = DataSubjectRequest.objects.get(account=self.provider_user)
        self.assertEqual(row.kind, DataSubjectRequest.Kind.EXPORT)
        self.assertEqual(row.status, DataSubjectRequest.Status.OPEN)
        event = DataSubjectRequestEvent.objects.get(request=row)
        self.assertEqual(event.action, "requested")
        self.assertEqual(event.actor, self.provider_user)

        response = self.client.get(reverse("data-subject-requests"))
        self.assertContains(response, "Export")
        self.assertIn("private", response.headers["Cache-Control"])
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_non_staff_cannot_open_staff_queue(self):
        self.client.force_login(self.provider_user)
        response = self.client.get(reverse("staff-data-subject-request-list"))
        self.assertEqual(response.status_code, 403)

    def test_staff_mfa_protected_queue_records_transitions(self):
        row = DataSubjectRequest.objects.create(
            account=self.provider_user,
            kind=DataSubjectRequest.Kind.DELETE,
        )
        DataSubjectRequestEvent.objects.create(
            request=row,
            actor=self.provider_user,
            action="requested",
        )

        self.client.force_login(self.staff_user)
        session = self.client.session
        session["staff_mfa_verified"] = True
        session.save()

        list_response = self.client.get(reverse("staff-data-subject-request-list"))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, "Delete")
        self.assertIn("no-store", list_response.headers["Cache-Control"])

        detail_url = reverse(
            "staff-data-subject-request-detail", kwargs={"request_id": row.pk}
        )
        start_response = self.client.post(
            detail_url,
            {"action": "start", "note": "Identity checked."},
        )
        self.assertRedirects(start_response, detail_url)
        row.refresh_from_db()
        self.assertEqual(row.status, DataSubjectRequest.Status.IN_PROGRESS)

        complete_response = self.client.post(
            detail_url,
            {"action": "complete", "note": "Retention review complete."},
        )
        self.assertRedirects(complete_response, detail_url)
        row.refresh_from_db()
        self.assertEqual(row.status, DataSubjectRequest.Status.COMPLETED)
        self.assertIsNotNone(row.completed_at)
        self.assertEqual(
            list(row.events.values_list("action", flat=True)),
            ["requested", "processing_started", "completed"],
        )

    def test_closed_request_cannot_be_changed_again(self):
        row = DataSubjectRequest.objects.create(
            account=self.provider_user,
            kind=DataSubjectRequest.Kind.ACCESS,
            status=DataSubjectRequest.Status.COMPLETED,
        )
        self.client.force_login(self.staff_user)
        session = self.client.session
        session["staff_mfa_verified"] = True
        session.save()
        detail_url = reverse(
            "staff-data-subject-request-detail", kwargs={"request_id": row.pk}
        )

        response = self.client.post(
            detail_url,
            {"action": "reject", "note": "Should not be accepted."},
        )
        self.assertEqual(response.status_code, 200)
        row.refresh_from_db()
        self.assertEqual(row.status, DataSubjectRequest.Status.COMPLETED)
        self.assertContains(response, "already closed")
