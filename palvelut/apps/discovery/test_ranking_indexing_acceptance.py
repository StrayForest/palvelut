from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.providers.models import Provider, ProviderService
from palvelut.apps.publishing.models import ProfileRevision
from palvelut.apps.taxonomy.models import Category


@override_settings(ALLOWED_HOSTS=["testserver"])
class DiscoveryRankingAndIndexingAcceptanceTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        category = Category.objects.get(slug="accounting")
        actor = get_user_model().objects.create_user(username="p2-ranking-reviewer")

        for index, display_name in enumerate(("Zulu Accounting", "Alpha Accounting", "Alpha Accounting"), start=1):
            provider = Provider.objects.create(
                provider_type=Provider.Type.BUSINESS,
                lifecycle=Provider.Lifecycle.PUBLISHED,
                claim_status=Provider.ClaimStatus.APPROVED,
                claim_evidence={"source": "test"},
                legal_name=f"Ranking Fixture {index} Oy",
                display_name=display_name,
                y_tunnus=f"100000{index}-{index}",
            )
            ProviderService.objects.create(
                provider=provider,
                category=category,
                title="Accounting",
                is_active=True,
            )
            revision = ProfileRevision.objects.create(
                provider=provider,
                status=ProfileRevision.Status.APPROVED,
                payload={"display_name": display_name, "about": "Ranking fixture"},
                created_by=actor,
                reviewed_at=timezone.now(),
            )
            ProviderReadDocument.objects.create(
                provider=provider,
                source_revision=revision,
                document=revision.payload,
            )

    def test_search_ranking_is_deterministic_and_filter_pages_are_noindex(self) -> None:
        response = self.client.get(
            "/palvelut/en/search/",
            {"q": "accounting", "language": "en"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["robots_meta"], "noindex,follow")

        documents = list(response.context["documents"])
        self.assertEqual(
            [(document.provider.display_name, document.provider_id) for document in documents],
            sorted(
                (document.provider.display_name, document.provider_id)
                for document in documents
            ),
        )
