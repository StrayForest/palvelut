from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from palvelut.apps.analytics.models import AnalyticsEvent
from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.publishing.models import ProfileRevision, ProviderSlug


@override_settings(
    ALLOWED_HOSTS=["testserver"],
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "p3-provider-dashboard-analytics",
        }
    },
)
class ProviderDashboardAnalyticsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.owner = user_model.objects.create_user(
            username="dashboard-owner@example.test",
            password="test-only-password",
        )
        cls.reviewer = user_model.objects.create_user(username="dashboard-reviewer")
        cls.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.PUBLISHED,
            claim_status=Provider.ClaimStatus.APPROVED,
            legal_name="Analytics Provider Oy",
            display_name="Analytics Provider",
            y_tunnus="3456789-0",
        )
        ProviderMembership.objects.create(
            provider=cls.provider,
            account=cls.owner,
            role=ProviderMembership.Role.OWNER,
        )
        approved = ProfileRevision.objects.create(
            provider=cls.provider,
            status=ProfileRevision.Status.APPROVED,
            payload={"display_name": "Analytics Provider", "about": "Analytics"},
            created_by=cls.reviewer,
            reviewed_at=timezone.now(),
        )
        ProviderReadDocument.objects.create(
            provider=cls.provider,
            source_revision=approved,
            document=approved.payload,
        )
        ProviderSlug.objects.create(
            provider=cls.provider,
            slug="analytics-provider",
            is_current=True,
        )
        ProfileRevision.objects.create(
            provider=cls.provider,
            status=ProfileRevision.Status.DRAFT,
            created_by=cls.owner,
            payload={
                "provider_type": "business",
                "legal_name": "Analytics Provider Oy",
                "display_name": "Analytics Provider",
                "contacts": [{"value": "+358401234567", "is_public": True}],
                "services": [{"is_active": True}],
                "service_areas": [{}],
                "languages": [{}],
                "media": [{"storage_key": "staged/example.webp"}],
            },
        )

    def setUp(self):
        cache.clear()
        AnalyticsEvent.objects.all().delete()

    def test_anonymous_cached_surfaces_record_every_visible_event(self):
        profile_url = "/palvelut/en/professionals/analytics-provider/"
        search_url = "/palvelut/en/search/?q=Analytics%20Provider"

        self.client.get(profile_url)
        self.client.get(profile_url)
        self.client.get(search_url)
        self.client.get(search_url)

        self.assertEqual(
            AnalyticsEvent.objects.filter(
                provider=self.provider,
                kind=AnalyticsEvent.Kind.PROFILE_VIEW,
            ).count(),
            2,
        )
        self.assertEqual(
            AnalyticsEvent.objects.filter(
                provider=self.provider,
                kind=AnalyticsEvent.Kind.IMPRESSION,
            ).count(),
            2,
        )

    def test_authenticated_public_reads_do_not_enter_provider_analytics(self):
        self.client.force_login(self.owner)
        self.client.get("/palvelut/en/professionals/analytics-provider/")
        self.client.get("/palvelut/en/search/?q=Analytics%20Provider")
        self.assertFalse(AnalyticsEvent.objects.exists())

    def test_workspace_shows_status_checklist_and_provider_scoped_aggregates(self):
        AnalyticsEvent.objects.bulk_create(
            [
                AnalyticsEvent(kind=AnalyticsEvent.Kind.IMPRESSION, provider=self.provider),
                AnalyticsEvent(kind=AnalyticsEvent.Kind.IMPRESSION, provider=self.provider),
                AnalyticsEvent(kind=AnalyticsEvent.Kind.PROFILE_VIEW, provider=self.provider),
                AnalyticsEvent(
                    kind=AnalyticsEvent.Kind.CONTACT_CLICK,
                    provider=self.provider,
                    channel="phone",
                ),
            ]
        )
        other = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.PUBLISHED,
            claim_status=Provider.ClaimStatus.APPROVED,
            legal_name="Other Oy",
            display_name="Other Provider",
            y_tunnus="4567890-1",
        )
        AnalyticsEvent.objects.create(
            kind=AnalyticsEvent.Kind.CONTACT_CLICK,
            provider=other,
            channel="email",
        )

        self.client.force_login(self.owner)
        response = self.client.get("/palvelut/account/profile/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertContains(response, "Analytics Provider")
        self.assertContains(response, "Published")
        self.assertContains(response, "6/6 complete")
        self.assertContains(response, "Impressions")
        self.assertContains(response, ">2<")
        self.assertContains(response, "Profile views")
        self.assertContains(response, "Contact clicks")
        self.assertNotContains(response, "Other Provider")
