from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.providers.models import (
    ContactChannel,
    Provider,
    ProviderService,
    ServiceArea,
)
from palvelut.apps.publishing.models import ProfileRevision, ProviderSlug
from palvelut.apps.taxonomy.models import Category, Municipality


@override_settings(ALLOWED_HOSTS=["testserver"])
class AnonymousDiscoveryContactAcceptanceTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        category = Category.objects.get(slug="accounting")
        city = Municipality.objects.get(region__country__code="FI", code="091")
        actor = get_user_model().objects.create_user(username="p2-acceptance-reviewer")

        cls.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.PUBLISHED,
            claim_status=Provider.ClaimStatus.APPROVED,
            claim_evidence={"source": "test"},
            legal_name="Acceptance Accounting Oy",
            display_name="Acceptance Accounting",
            y_tunnus="2345678-2",
        )
        ProviderService.objects.create(
            provider=cls.provider,
            category=category,
            title="Accounting",
            is_active=True,
        )
        ServiceArea.objects.create(
            provider=cls.provider,
            municipality=city,
            mode=ServiceArea.Mode.ONSITE,
        )
        revision = ProfileRevision.objects.create(
            provider=cls.provider,
            status=ProfileRevision.Status.APPROVED,
            payload={
                "display_name": "Acceptance Accounting",
                "about": "Acceptance flow fixture",
            },
            created_by=actor,
            reviewed_at=timezone.now(),
        )
        ProviderReadDocument.objects.create(
            provider=cls.provider,
            source_revision=revision,
            document=revision.payload,
        )
        ProviderSlug.objects.create(
            provider=cls.provider,
            slug="acceptance-accounting",
            is_current=True,
        )
        ContactChannel.objects.create(
            provider=cls.provider,
            kind=ContactChannel.Kind.EMAIL,
            value="contact@example.test",
            label="Email",
            is_public=True,
        )

    def test_anonymous_user_reaches_relevant_contact_in_three_actions(self) -> None:
        home = self.client.get("/palvelut/en/")
        self.assertEqual(home.status_code, 200)
        self.assertContains(home, 'action="/palvelut/en/search/"', html=False)

        # Action 1: submit the two-field discovery search.
        results = self.client.get(
            "/palvelut/en/search/",
            {"q": "accounting", "city": "Helsinki"},
        )
        self.assertEqual(results.status_code, 200)
        profile_path = "/palvelut/en/professionals/acceptance-accounting/"
        self.assertContains(results, profile_path)

        # Action 2: open the relevant provider profile.
        profile = self.client.get(profile_path)
        self.assertEqual(profile.status_code, 200)
        contact_path = f"/palvelut/en/go/{self.provider.id}/email/"
        self.assertContains(profile, contact_path)

        # Action 3: activate the structured contact link.
        contact = self.client.get(contact_path)
        self.assertEqual(contact.status_code, 302)
        self.assertEqual(contact["Location"], "mailto:contact@example.test")

    def test_core_flow_is_native_html_with_progressive_htmx_contract(self) -> None:
        home = self.client.get("/palvelut/en/")
        self.assertContains(home, 'hx-boost="true"', html=False)
        self.assertContains(home, 'hx-push-url="true"', html=False)
        self.assertContains(home, 'hx-target="#main-content"', html=False)
        self.assertContains(home, 'hx-select="#main-content"', html=False)
        self.assertContains(home, 'id="service-query"', html=False)
        self.assertContains(home, 'id="city-query"', html=False)
        self.assertContains(home, 'method="get"', html=False)

        results = self.client.get(
            "/palvelut/en/search/",
            {"q": "accounting", "city": "Helsinki"},
        )
        self.assertEqual(results.status_code, 200)
        self.assertContains(results, 'id="service-query"', html=False)
        self.assertContains(results, 'id="city-query"', html=False)
        self.assertContains(results, 'value="accounting"', html=False)
        self.assertContains(results, 'value="Helsinki"', html=False)

        profile = self.client.get("/palvelut/en/professionals/acceptance-accounting/")
        self.assertEqual(profile.status_code, 200)
        self.assertContains(profile, 'hx-boost="false"', html=False)
