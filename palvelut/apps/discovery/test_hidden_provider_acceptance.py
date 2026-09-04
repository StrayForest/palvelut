from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.providers.models import Provider, ProviderService, ServiceArea
from palvelut.apps.publishing.models import ProfileRevision, ProviderSlug
from palvelut.apps.taxonomy.models import Category, Municipality


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "hidden-provider-acceptance-tests",
        }
    },
)
class HiddenProviderAcceptanceTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.category = Category.objects.get(slug="accounting")
        cls.city = Municipality.objects.get(region__country__code="FI", code="091")
        actor = get_user_model().objects.create_user(
            username="hidden-provider-reviewer"
        )

        for index, lifecycle in enumerate(
            (Provider.Lifecycle.DRAFT, Provider.Lifecycle.SUSPENDED),
            start=1,
        ):
            provider = Provider.objects.create(
                provider_type=Provider.Type.BUSINESS,
                lifecycle=lifecycle,
                claim_status=Provider.ClaimStatus.APPROVED,
                claim_evidence={"source": "test"},
                legal_name=f"Hidden {lifecycle} Accounting Oy",
                display_name=f"Hidden {lifecycle} Accounting",
                y_tunnus=f"345678{index}-{index}",
            )
            ProviderService.objects.create(
                provider=provider,
                category=cls.category,
                title="Accounting",
                is_active=True,
            )
            ServiceArea.objects.create(
                provider=provider,
                municipality=cls.city,
                mode=ServiceArea.Mode.ONSITE,
            )
            revision = ProfileRevision.objects.create(
                provider=provider,
                status=ProfileRevision.Status.APPROVED,
                payload={
                    "display_name": f"Hidden {lifecycle} Accounting",
                    "about": "Must never be public",
                },
                created_by=actor,
                reviewed_at=timezone.now(),
            )
            ProviderReadDocument.objects.create(
                provider=provider,
                source_revision=revision,
                document=revision.payload,
            )
            ProviderSlug.objects.create(
                provider=provider,
                slug=f"hidden-{lifecycle}-accounting",
                is_current=True,
            )

    def setUp(self) -> None:
        cache.clear()

    def assert_hidden_names_absent(self, response) -> None:
        self.assertNotContains(response, "Hidden draft Accounting")
        self.assertNotContains(response, "Hidden suspended Accounting")

    def test_hidden_providers_never_reach_html_schema_sitemap_or_cache(self) -> None:
        search_path = "/palvelut/en/search/?q=accounting&city=Helsinki"
        first_search = self.client.get(search_path)
        self.assertEqual(first_search.status_code, 200)
        self.assert_hidden_names_absent(first_search)
        self.assertNotContains(first_search, '"@type":"LocalBusiness"', html=False)

        cached_search = self.client.get(search_path)
        self.assertEqual(cached_search.status_code, 200)
        self.assert_hidden_names_absent(cached_search)

        landing = self.client.get("/palvelut/en/helsinki/accounting/")
        self.assertEqual(landing.status_code, 200)
        self.assert_hidden_names_absent(landing)

        sitemap = self.client.get("/palvelut/sitemap.xml")
        self.assertEqual(sitemap.status_code, 200)
        self.assertNotContains(sitemap, "hidden-draft-accounting")
        self.assertNotContains(sitemap, "hidden-suspended-accounting")

        for lifecycle in (Provider.Lifecycle.DRAFT, Provider.Lifecycle.SUSPENDED):
            path = f"/palvelut/en/professionals/hidden-{lifecycle}-accounting/"
            first_profile = self.client.get(path)
            self.assertEqual(first_profile.status_code, 404)
            self.assertNotContains(
                first_profile,
                '"@type":"LocalBusiness"',
                html=False,
                status_code=404,
            )

            second_profile = self.client.get(path)
            self.assertEqual(second_profile.status_code, 404)
