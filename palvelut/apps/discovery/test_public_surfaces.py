from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.providers.models import (
    Provider,
    ProviderLanguage,
    ProviderService,
    ServiceArea,
)
from palvelut.apps.publishing.models import ProfileRevision, ProviderSlug
from palvelut.apps.taxonomy.models import (
    Category,
    CategorySynonym,
    Language,
    Municipality,
)


@override_settings(ALLOWED_HOSTS=["testserver"])
class PublicDiscoverySurfaceTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.category = Category.objects.get(slug="accounting")
        cls.city = Municipality.objects.get(region__country__code="FI", code="091")
        cls.espoo = Municipality.objects.get(region__country__code="FI", name="Espoo")
        cls.english = Language.objects.get(code="en")
        CategorySynonym.objects.get_or_create(
            category=cls.category,
            locale="en",
            value="bookkeeper",
        )
        actor = get_user_model().objects.create_user(username="discovery-reviewer")
        cls.published = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.PUBLISHED,
            claim_status=Provider.ClaimStatus.APPROVED,
            claim_evidence={"source": "test"},
            legal_name="Public Accounting Oy",
            display_name="Public Accounting",
            y_tunnus="1234567-1",
        )
        ProviderService.objects.create(
            provider=cls.published,
            category=cls.category,
            title="Accounting",
            is_active=True,
        )
        ServiceArea.objects.create(
            provider=cls.published,
            municipality=cls.city,
            mode=ServiceArea.Mode.ONSITE,
        )
        ServiceArea.objects.create(
            provider=cls.published,
            municipality=cls.espoo,
            mode=ServiceArea.Mode.REMOTE,
        )
        ProviderLanguage.objects.create(
            provider=cls.published,
            language=cls.english,
        )
        revision = ProfileRevision.objects.create(
            provider=cls.published,
            status=ProfileRevision.Status.APPROVED,
            payload={
                "display_name": "Approved Public Accounting",
                "about": "Approved copy",
            },
            created_by=actor,
            reviewed_at=timezone.now(),
        )
        ProviderReadDocument.objects.create(
            provider=cls.published,
            source_revision=revision,
            document=revision.payload,
        )
        ProviderSlug.objects.create(
            provider=cls.published,
            slug="public-accounting",
            is_current=True,
        )

        hidden = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.SUSPENDED,
            claim_status=Provider.ClaimStatus.APPROVED,
            claim_evidence={"source": "test"},
            legal_name="Hidden Accounting Oy",
            display_name="Hidden Accounting",
            y_tunnus="1234568-2",
        )
        hidden_revision = ProfileRevision.objects.create(
            provider=hidden,
            status=ProfileRevision.Status.APPROVED,
            payload={"display_name": "Hidden Accounting"},
            created_by=actor,
            reviewed_at=timezone.now(),
        )
        ProviderReadDocument.objects.create(
            provider=hidden,
            source_revision=hidden_revision,
            document=hidden_revision.payload,
        )

    def test_home_exposes_two_field_search_without_authentication(self) -> None:
        response = self.client.get("/palvelut/en/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="q"', html=False)
        self.assertContains(response, 'name="city"', html=False)

    def test_synonym_search_returns_only_published_read_documents(self) -> None:
        response = self.client.get(
            "/palvelut/en/search/",
            {"q": "  bookkeeper  ", "city": "Helsinki"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approved Public Accounting")
        self.assertNotContains(response, "Hidden Accounting")

    def test_typo_tolerant_synonym_matches_category(self) -> None:
        response = self.client.get(
            "/palvelut/en/search/",
            {"q": "bookkeper", "city": "Helsinki"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approved Public Accounting")

    def test_language_and_service_mode_filters_are_combined(self) -> None:
        matching = self.client.get(
            "/palvelut/en/search/",
            {
                "q": "bookkeeper",
                "city": "Helsinki",
                "language": "EN",
                "mode": "onsite",
            },
        )
        self.assertEqual(matching.status_code, 200)
        self.assertContains(matching, "Approved Public Accounting")

        wrong_mode = self.client.get(
            "/palvelut/en/search/",
            {
                "q": "bookkeeper",
                "city": "Helsinki",
                "language": "en",
                "mode": "remote",
            },
        )
        self.assertEqual(wrong_mode.status_code, 200)
        self.assertNotContains(wrong_mode, "Approved Public Accounting")
        self.assertContains(wrong_mode, "Show all service modes")
        self.assertContains(
            wrong_mode,
            "/palvelut/en/search/?q=bookkeeper&amp;city=Helsinki&amp;language=en",
            html=False,
        )

    def test_invalid_explicit_filter_does_not_fall_back_to_unrelated_results(
        self,
    ) -> None:
        response = self.client.get(
            "/palvelut/en/search/",
            {"category": "does-not-exist"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Approved Public Accounting")
        self.assertContains(response, "Search all categories")

    def test_city_category_landing_and_profile_are_server_rendered(self) -> None:
        landing = self.client.get("/palvelut/en/helsinki/accounting/")
        self.assertEqual(landing.status_code, 200)
        self.assertContains(landing, "Approved Public Accounting")
        self.assertContains(
            landing,
            "/palvelut/en/professionals/public-accounting/",
        )

        profile = self.client.get("/palvelut/en/professionals/public-accounting/")
        self.assertEqual(profile.status_code, 200)
        self.assertContains(profile, "Approved Public Accounting")
        self.assertContains(profile, "Approved copy")

    def test_suspended_provider_profile_is_not_public(self) -> None:
        ProviderSlug.objects.create(
            provider=Provider.objects.get(legal_name="Hidden Accounting Oy"),
            slug="hidden-accounting",
            is_current=True,
        )
        response = self.client.get("/palvelut/en/professionals/hidden-accounting/")
        self.assertEqual(response.status_code, 404)
