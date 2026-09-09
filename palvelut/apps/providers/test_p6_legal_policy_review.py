from django.test import TestCase
from django.urls import reverse

from palvelut.apps.moderation.forms import ContentReportForm
from palvelut.apps.providers.claim_services import CURRENT_PROVIDER_TERMS_VERSION


class P6LegalPolicyReviewTests(TestCase):
    def test_privacy_notice_covers_current_beta_provider_evidence(self) -> None:
        response = self.client.get(
            reverse(
                "legal-document",
                kwargs={"locale": "en", "document": "privacy"},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aleksei Lisitcin")
        self.assertContains(response, "ownership-control evidence")
        self.assertContains(response, "professional-right reference")
        self.assertContains(response, "employer-authorization reference")
        self.assertContains(response, "Ownership and eligibility evidence is kept private")
        self.assertContains(response, "Raw product-analytics events expire after 90 days")
        self.assertContains(response, "Manage data requests")

    def test_provider_terms_publish_the_same_version_enforced_by_claim_review(self) -> None:
        response = self.client.get(
            reverse(
                "legal-document",
                kwargs={"locale": "en", "document": "terms"},
            )
        )

        self.assertEqual(CURRENT_PROVIDER_TERMS_VERSION, "2026-09-10")
        self.assertContains(
            response,
            f"Current provider-terms version: {CURRENT_PROVIDER_TERMS_VERSION}.",
        )
        self.assertContains(response, "must have an active Finnish Y-tunnus")
        self.assertContains(response, "employer authorization to list services")
        self.assertContains(response, "Finrix Palvelut is not a party to that service contract")
        self.assertContains(response, "Ownership approval does not publish a profile")
        self.assertContains(response, "a new version is issued")

    def test_public_report_form_uses_neutral_policy_wording_and_data_minimization_hint(self) -> None:
        form = ContentReportForm()

        self.assertEqual(form.fields["category"].label, "What is the problem?")
        self.assertEqual(
            list(form.fields["category"].choices),
            [
                ("incorrect_content", "Incorrect or outdated information"),
                ("impersonation", "Impersonation or ownership concern"),
                ("illegal_or_harmful", "Suspected illegal or harmful content"),
                ("other", "Other directory-policy concern"),
            ],
        )
        self.assertIn(
            "Do not include unnecessary sensitive personal data",
            str(form.fields["details"].help_text),
        )
