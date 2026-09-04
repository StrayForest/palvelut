from __future__ import annotations

from math import ceil
from time import perf_counter

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.discovery.views import SearchState, _filtered_documents
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision

BETA_PROVIDER_COUNT = 50
CACHED_TTFB_P95_MS = 300
UNCACHED_RESPONSE_P95_MS = 800
SEARCH_QUERY_P95_MS = 300


def _p95_ms(samples: list[float]) -> float:
    ordered = sorted(samples)
    return ordered[ceil(len(ordered) * 0.95) - 1] * 1000


@override_settings(ALLOWED_HOSTS=["testserver"])
class DiscoveryPerformanceAcceptanceTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        actor = get_user_model().objects.create_user(username="p2-performance-reviewer")
        reviewed_at = timezone.now()

        for index in range(BETA_PROVIDER_COUNT):
            display_name = f"Performance Provider {index:02d}"
            provider = Provider.objects.create(
                provider_type=Provider.Type.BUSINESS,
                lifecycle=Provider.Lifecycle.PUBLISHED,
                claim_status=Provider.ClaimStatus.APPROVED,
                claim_evidence={"source": "performance-fixture"},
                legal_name=f"Performance Fixture {index:02d} Oy",
                display_name=display_name,
                y_tunnus=f"2000{index:04d}-{index % 10}",
            )
            revision = ProfileRevision.objects.create(
                provider=provider,
                status=ProfileRevision.Status.APPROVED,
                payload={"display_name": display_name, "about": "Performance fixture"},
                created_by=actor,
                reviewed_at=reviewed_at,
            )
            ProviderReadDocument.objects.create(
                provider=provider,
                source_revision=revision,
                document=revision.payload,
            )

    def tearDown(self) -> None:
        cache.clear()
        super().tearDown()

    def test_beta_sized_discovery_stays_within_latency_budgets(self) -> None:
        self.assertEqual(ProviderReadDocument.objects.count(), BETA_PROVIDER_COUNT)
        path = "/palvelut/en/search/?q=Performance"

        # Prime Django/template imports before collecting timings.
        cache.clear()
        warmup = self.client.get(path)
        self.assertEqual(warmup.status_code, 200)

        uncached_samples: list[float] = []
        for _ in range(20):
            cache.clear()
            started = perf_counter()
            response = self.client.get(path)
            uncached_samples.append(perf_counter() - started)
            self.assertEqual(response.status_code, 200)

        cache.clear()
        primed = self.client.get(path)
        self.assertEqual(primed.status_code, 200)
        cached_samples: list[float] = []
        for _ in range(30):
            started = perf_counter()
            response = self.client.get(path)
            cached_samples.append(perf_counter() - started)
            self.assertEqual(response.status_code, 200)

        state = SearchState(
            query="Performance",
            category=None,
            municipality=None,
            language_code="",
            mode="",
        )
        query_samples: list[float] = []
        for _ in range(30):
            started = perf_counter()
            provider_ids = list(
                _filtered_documents(state).values_list("provider_id", flat=True)
            )
            query_samples.append(perf_counter() - started)
            self.assertEqual(len(provider_ids), BETA_PROVIDER_COUNT)

        cached_p95 = _p95_ms(cached_samples)
        uncached_p95 = _p95_ms(uncached_samples)
        query_p95 = _p95_ms(query_samples)

        self.assertLessEqual(
            cached_p95,
            CACHED_TTFB_P95_MS,
            f"cached discovery p95 {cached_p95:.1f} ms exceeds {CACHED_TTFB_P95_MS} ms",
        )
        self.assertLessEqual(
            uncached_p95,
            UNCACHED_RESPONSE_P95_MS,
            f"uncached discovery p95 {uncached_p95:.1f} ms exceeds {UNCACHED_RESPONSE_P95_MS} ms",
        )
        self.assertLessEqual(
            query_p95,
            SEARCH_QUERY_P95_MS,
            f"search query p95 {query_p95:.1f} ms exceeds {SEARCH_QUERY_P95_MS} ms",
        )
