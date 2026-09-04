from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.providers.models import Provider, ProviderService, ServiceArea
from palvelut.apps.publishing.models import ProfileRevision, ProviderSlug
from palvelut.apps.taxonomy.models import Category, Municipality


@override_settings(ALLOWED_HOSTS=["testserver"])
class DiscoverySeoMetadataTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.category = Category.objects.get(slug="accounting")
        cls.city = Municipality.objects.get(region__country__code="FI", code="091")
        actor = get_user_model().objects.create_user(username="seo-reviewer")
        cls.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.PUBLISHED,
            claim_status=Provider.ClaimStatus.APPROVED,
            claim_evidence={"source": "test"},
            legal_name="SEO Accounting Oy",
            display_name="SEO Accounting",
            y_tunnus="7654321-0",
        )
        ProviderService.objects.create(
            provider=cls.provider,
            category=cls.category,
            title="Accounting",
            is_active=True,
        )
        ServiceArea.objects.create(
            provider=cls.provider,
            municipality=cls.city,
            mode=ServiceArea.Mode.ONSITE,
        )
        revision = ProfileRevision.objects.create(
            provider=cls.provider,
            status=ProfileRevision.Status.APPROVED,
            payload={"display_name": "SEO Accounting", "about": "Approved SEO copy"},
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
            slug="seo-accounting-old",
            is_current=False,
        )
        ProviderSlug.objects.create(
            provider=cls.provider,
            slug="seo-accounting",
            is_current=True,
        )

    def test_profile_has_canonical_hreflang_and_localbusiness_schema(self) -> None:
        response = self.client.get("/palvelut/en/professionals/seo-accounting/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<link rel="canonical" '
            'href="https://finrix.fi/palvelut/en/professionals/seo-accounting/">',
            html=False,
        )
        self.assertContains(response, 'hreflang="fi"', html=False)
        self.assertContains(response, 'hreflang="ru"', html=False)
        self.assertContains(response, 'hreflang="en"', html=False)
        self.assertContains(response, '"@type":"LocalBusiness"', html=False)
        self.assertNotContains(response, "aggregateRating")

    def test_old_provider_slug_permanently_redirects_to_current_slug(self) -> None:
        response = self.client.get("/palvelut/en/professionals/seo-accounting-old/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response["Location"],
            "/palvelut/en/professionals/seo-accounting/",
        )

    def test_search_and_thin_city_category_are_noindex(self) -> None:
        search = self.client.get("/palvelut/en/search/?q=accounting")
        self.assertContains(
            search,
            '<meta name="robots" content="noindex,follow">',
            html=False,
        )

        landing = self.client.get("/palvelut/en/helsinki/accounting/")
        self.assertEqual(landing.status_code, 200)
        self.assertContains(
            landing,
            '<meta name="robots" content="noindex,follow">',
            html=False,
        )

    def test_sitemap_contains_published_profile_but_not_thin_landing_or_search(
        self,
    ) -> None:
        response = self.client.get("/palvelut/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn(
            "https://finrix.fi/palvelut/en/professionals/seo-accounting/",
            body,
        )
        self.assertNotIn("/en/helsinki/accounting/", body)
        self.assertNotIn("/search/", body)
        self.assertNotIn("seo-accounting-old", body)

    def test_robots_points_at_prefixed_sitemap(self) -> None:
        response = self.client.get("/palvelut/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Sitemap: https://finrix.fi/palvelut/sitemap.xml",
            html=False,
        )
