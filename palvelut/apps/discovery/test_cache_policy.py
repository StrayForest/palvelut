from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision, ProviderSlug


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "discovery-cache-policy-tests",
        }
    },
)
class PublicDiscoveryCachePolicyTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        user_model = get_user_model()
        cls.viewer = user_model.objects.create_user(
            username="cache-authenticated-viewer",
            password="test-only-password",
        )
        reviewer = user_model.objects.create_user(username="cache-reviewer")
        cls.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.PUBLISHED,
            claim_status=Provider.ClaimStatus.APPROVED,
            claim_evidence={"source": "test"},
            legal_name="Cache Policy Oy",
            display_name="Cache Policy",
            y_tunnus="2345678-9",
        )
        revision = ProfileRevision.objects.create(
            provider=cls.provider,
            status=ProfileRevision.Status.APPROVED,
            payload={"display_name": "Cached Provider", "about": "Cached copy"},
            created_by=reviewer,
            reviewed_at=timezone.now(),
        )
        cls.document = ProviderReadDocument.objects.create(
            provider=cls.provider,
            source_revision=revision,
            document=revision.payload,
        )
        ProviderSlug.objects.create(
            provider=cls.provider,
            slug="cache-policy",
            is_current=True,
        )

    def setUp(self) -> None:
        cache.clear()

    def test_anonymous_public_surfaces_expose_expected_cache_headers(self) -> None:
        home = self.client.get("/palvelut/en/")
        profile = self.client.get("/palvelut/en/professionals/cache-policy/")
        search = self.client.get("/palvelut/en/search/?q=cache")

        self.assertEqual(
            home["Cache-Control"],
            "public, max-age=0, s-maxage=3600, stale-while-revalidate=3600",
        )
        self.assertEqual(
            profile["Cache-Control"],
            "public, max-age=0, s-maxage=300, stale-while-revalidate=86400",
        )
        self.assertEqual(search["Cache-Control"], "public, max-age=0, s-maxage=0")

    def test_anonymous_profile_is_read_through_cached(self) -> None:
        first = self.client.get("/palvelut/en/professionals/cache-policy/")
        self.assertContains(first, "Cached Provider")

        self.document.document = {"display_name": "Fresh Provider", "about": "Fresh copy"}
        self.document.save(update_fields=["document"])

        second = self.client.get("/palvelut/en/professionals/cache-policy/")
        self.assertContains(second, "Cached Provider")
        self.assertNotContains(second, "Fresh Provider")

    def test_authenticated_request_bypasses_public_cache_and_is_private(self) -> None:
        first = self.client.get("/palvelut/en/professionals/cache-policy/")
        self.assertContains(first, "Cached Provider")

        self.document.document = {"display_name": "Fresh Provider", "about": "Fresh copy"}
        self.document.save(update_fields=["document"])

        self.client.force_login(self.viewer)
        authenticated = self.client.get("/palvelut/en/professionals/cache-policy/")

        self.assertContains(authenticated, "Fresh Provider")
        self.assertEqual(authenticated["Cache-Control"], "private, no-store")
        self.assertIn("Cookie", authenticated.get("Vary", ""))

        self.client.logout()
        anonymous_again = self.client.get("/palvelut/en/professionals/cache-policy/")
        self.assertContains(anonymous_again, "Cached Provider")
        self.assertNotContains(anonymous_again, "Fresh Provider")

    def test_search_cache_key_includes_query_string(self) -> None:
        first = self.client.get("/palvelut/en/search/?q=cache")
        second = self.client.get("/palvelut/en/search/?q=missing")

        self.assertContains(first, "Cached Provider")
        self.assertNotContains(second, "Cached Provider")
