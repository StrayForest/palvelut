from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.discovery.views import SearchState, _filtered_documents
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision


class P2QueryPlanGateTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        actor = get_user_model().objects.create_user(username="p2-query-plan-reviewer")
        provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.PUBLISHED,
            claim_status=Provider.ClaimStatus.APPROVED,
            claim_evidence={"source": "p2-query-plan-gate"},
            legal_name="P2 Query Plan Fixture Oy",
            display_name="P2 Query Plan Fixture",
            y_tunnus="2999999-9",
        )
        revision = ProfileRevision.objects.create(
            provider=provider,
            status=ProfileRevision.Status.APPROVED,
            payload={"display_name": provider.display_name},
            created_by=actor,
            reviewed_at=timezone.now(),
        )
        ProviderReadDocument.objects.create(
            provider=provider,
            source_revision=revision,
            document=revision.payload,
        )

    def test_public_search_query_has_inspectable_postgres_plan(self) -> None:
        state = SearchState(
            query="P2 Query Plan",
            category=None,
            municipality=None,
            language_code="",
            mode="",
        )
        queryset = _filtered_documents(state)
        plan = json.loads(queryset.explain(format="json"))

        self.assertEqual(len(plan), 1)
        self.assertIn("Plan", plan[0])
        self.assertGreaterEqual(plan[0]["Plan"]["Plan Rows"], 0)
        self.assertEqual(
            list(queryset.values_list("provider_id", flat=True)), [self.provider_id]
        )

    @property
    def provider_id(self):
        return Provider.objects.get(legal_name="P2 Query Plan Fixture Oy").id
