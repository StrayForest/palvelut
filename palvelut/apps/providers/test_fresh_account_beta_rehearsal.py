from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from palvelut.apps.analytics.models import AnalyticsEvent
from palvelut.apps.providers.claim_services import resolve_provider_claim
from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.publishing.models import ProfileRevision, ProviderSlug
from palvelut.apps.publishing.workflow import approve_revision
from palvelut.apps.taxonomy.models import Category, Language, Municipality


class FreshAccountBetaRehearsalTests(TestCase):
    EMAIL = "p6-beta-rehearsal@example.test"
    PASSWORD = "P6-beta-rehearsal-pass-2026!"  # test-only

    def test_fresh_account_reaches_public_profile_and_tracked_contact(self):
        user_model = get_user_model()
        self.assertFalse(user_model.objects.filter(username=self.EMAIL).exists())

        registered = self.client.post(
            reverse("account-register"),
            {
                "email": self.EMAIL,
                "password1": self.PASSWORD,
                "password2": self.PASSWORD,
            },
        )
        self.assertEqual(registered.status_code, 201)
        account = user_model.objects.get(username=self.EMAIL)
        self.assertFalse(account.is_active)
        self.assertFalse(ProviderMembership.objects.filter(account=account).exists())
        self.assertEqual(len(mail.outbox), 1)

        verification_url = mail.outbox[0].body.strip().split()[-1]
        verification_path = verification_url.split("testserver", 1)[1]
        verified = self.client.get(verification_path)
        self.assertRedirects(verified, reverse("account-login"))
        account.refresh_from_db()
        self.assertTrue(account.is_active)

        logged_in = self.client.post(
            reverse("account-login"),
            {"username": self.EMAIL, "password": self.PASSWORD},
        )
        self.assertRedirects(logged_in, reverse("provider-workspace"))
        self.assertFalse(ProviderMembership.objects.filter(account=account).exists())

        claim_started = self.client.post(
            reverse("account-provider-start"),
            {
                "provider_type": Provider.Type.BUSINESS,
                "legal_name": "P6 Beta Rehearsal Oy",
                "display_name": "P6 Beta Rehearsal",
                "y_tunnus": "1357924-6",
                "evidence_kind": "registry_signatory",
                "evidence_reference": "Synthetic PRH signatory evidence for P6 rehearsal",
                "provider_terms_accepted": "on",
            },
        )
        self.assertRedirects(claim_started, reverse("provider-workspace"))
        provider = Provider.objects.get(legal_name="P6 Beta Rehearsal Oy")
        self.assertEqual(provider.claim_status, Provider.ClaimStatus.PENDING)
        self.assertFalse(ProviderMembership.objects.filter(account=account).exists())

        staff = user_model.objects.create_user(
            username="p6-rehearsal-staff@example.test",
            email="p6-rehearsal-staff@example.test",
            password="staff-test-only-pass",
            is_staff=True,
        )
        resolve_provider_claim(
            provider_id=provider.pk,
            actor=staff,
            decision="approve",
            review_note="P6 fresh-account beta rehearsal ownership approval",
        )
        provider.refresh_from_db()
        membership = ProviderMembership.objects.get(account=account, provider=provider)
        self.assertTrue(membership.is_active)
        self.assertEqual(membership.role, ProviderMembership.Role.OWNER)

        category = Category.objects.get(slug="accounting")
        municipality = Municipality.objects.get(region__country__code="FI", code="091")
        language = Language.objects.get(code="ru")
        edit = self.client.post(
            reverse("provider-workspace-edit", args=[provider.pk]),
            {
                "provider_type": Provider.Type.BUSINESS,
                "legal_name": "P6 Beta Rehearsal Oy",
                "display_name": "P6 Beta Rehearsal",
                "y_tunnus": "1357924-6",
                "primary_category": str(category.pk),
                "service_title": "Accounting rehearsal",
                "service_description": "Synthetic end-to-end beta rehearsal service.",
                "price_text": "From 90 EUR",
                "primary_municipality": str(municipality.pk),
                "service_mode": "onsite",
                "service_language": str(language.pk),
                "contact_kind": "email",
                "contact_value": "p6-contact@example.test",
                "contacts": "[]",
                "services": "[]",
                "service_areas": "[]",
                "languages": "[]",
            },
        )
        self.assertEqual(edit.status_code, 302)

        preview = self.client.get(
            reverse("provider-workspace-preview", args=[provider.pk])
        )
        self.assertContains(preview, "P6 Beta Rehearsal")
        self.assertContains(preview, "Accounting rehearsal")

        submitted = self.client.post(
            reverse("provider-workspace-submit", args=[provider.pk])
        )
        self.assertEqual(submitted.status_code, 302)
        revision = ProfileRevision.objects.get(
            provider=provider, status=ProfileRevision.Status.PENDING
        )
        approve_revision(revision_id=revision.pk, actor=staff)

        provider.refresh_from_db()
        self.assertEqual(provider.lifecycle, Provider.Lifecycle.PUBLISHED)
        slug = ProviderSlug.objects.get(provider=provider, is_current=True)

        public_profile = self.client.get(
            reverse("provider-profile", kwargs={"locale": "en", "slug": slug.slug})
        )
        self.assertContains(public_profile, "P6 Beta Rehearsal")
        discovery = self.client.get(
            reverse("discovery-search", kwargs={"locale": "en"}),
            {"q": "P6 Beta Rehearsal"},
        )
        self.assertContains(discovery, "P6 Beta Rehearsal")

        tracked_contact = self.client.get(
            reverse(
                "contact-redirect",
                kwargs={
                    "locale": "en",
                    "provider_id": provider.pk,
                    "channel": "email",
                },
            )
        )
        self.assertEqual(tracked_contact.status_code, 302)
        self.assertEqual(tracked_contact.headers["Location"], "mailto:p6-contact@example.test")
        self.assertTrue(
            AnalyticsEvent.objects.filter(
                provider=provider,
                kind=AnalyticsEvent.Kind.CONTACT_CLICK,
                channel="email",
            ).exists()
        )
