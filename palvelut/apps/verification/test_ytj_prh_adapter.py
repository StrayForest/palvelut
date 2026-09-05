from __future__ import annotations

from collections import deque

from django.contrib.auth import get_user_model
from django.test import TestCase

from palvelut.apps.providers.models import Provider

from .adapters import (
    PRH_YTJ_SOURCE,
    RegistryOutcome,
    TransportResponse,
    YtjPrhAdapter,
)
from .models import VerificationCheck
from .services import run_ytj_business_identity_check


class FakeTransport:
    def __init__(self, responses: list[TransportResponse | Exception]) -> None:
        self.responses = deque(responses)
        self.calls: list[tuple[str, float]] = []

    def get_json(self, url: str, *, timeout_seconds: float) -> TransportResponse:
        self.calls.append((url, timeout_seconds))
        response = self.responses.popleft()
        if isinstance(response, Exception):
            raise response
        return response


class YtjPrhAdapterTests(TestCase):
    def test_success_preserves_source_snapshot_and_metadata(self) -> None:
        payload = {
            "companies": [
                {
                    "businessId": "0112038-9",
                    "names": [{"name": "Example Oy"}],
                }
            ]
        }
        transport = FakeTransport([TransportResponse(200, payload)])
        result = YtjPrhAdapter(transport=transport, sleep=lambda _: None).lookup_business_id(
            "0112038-9"
        )

        self.assertEqual(result.outcome, RegistryOutcome.FOUND)
        self.assertEqual(result.attempts, 1)
        self.assertEqual(result.source_snapshot, payload)
        metadata = result.evidence_metadata()
        self.assertEqual(metadata["source"], PRH_YTJ_SOURCE)
        self.assertEqual(metadata["business_id"], "0112038-9")
        self.assertEqual(metadata["source_snapshot"], payload)
        self.assertFalse(metadata["manual_fallback_required"])
        self.assertIn("businessId=0112038-9", result.source_url)

    def test_transient_failure_retries_only_to_bound_then_requires_manual_review(self) -> None:
        transport = FakeTransport(
            [
                TransportResponse(503, {"error": "one"}),
                TransportResponse(503, {"error": "two"}),
                TransportResponse(503, {"error": "three"}),
            ]
        )
        result = YtjPrhAdapter(transport=transport, sleep=lambda _: None).lookup_business_id(
            "0112038-9"
        )

        self.assertEqual(len(transport.calls), 3)
        self.assertEqual(result.attempts, 3)
        self.assertEqual(result.outcome, RegistryOutcome.MANUAL_REVIEW)
        self.assertTrue(result.evidence_metadata()["manual_fallback_required"])
        self.assertEqual(result.status_code, 503)

    def test_successful_response_without_business_id_is_a_factual_not_found(self) -> None:
        transport = FakeTransport([TransportResponse(200, {"companies": []})])
        result = YtjPrhAdapter(transport=transport).lookup_business_id("0112038-9")
        self.assertEqual(result.outcome, RegistryOutcome.NOT_FOUND)
        self.assertEqual(result.status_code, 200)

    def test_retry_and_timeout_configuration_cannot_exceed_safety_bounds(self) -> None:
        with self.assertRaises(ValueError):
            YtjPrhAdapter(max_attempts=4)
        with self.assertRaises(ValueError):
            YtjPrhAdapter(timeout_seconds=5.0)


class YtjPrhVerificationServiceTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.staff = user_model.objects.create_user(username="ytj-staff", is_staff=True)
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Example Oy",
            display_name="Example",
            y_tunnus="0112038-9",
        )

    def test_found_result_records_verified_check_with_snapshot(self) -> None:
        payload = {"companies": [{"businessId": self.provider.y_tunnus}]}
        adapter = YtjPrhAdapter(
            transport=FakeTransport([TransportResponse(200, payload)]),
            sleep=lambda _: None,
        )

        check = run_ytj_business_identity_check(
            provider_id=self.provider.pk,
            actor=self.staff,
            adapter=adapter,
        )

        self.assertEqual(check.status, VerificationCheck.Status.VERIFIED)
        self.assertEqual(check.evidence_metadata["source_snapshot"], payload)
        self.assertEqual(check.evidence_metadata["source"], PRH_YTJ_SOURCE)
        self.assertFalse(check.evidence_metadata["manual_fallback_required"])
        self.assertEqual(check.events.count(), 1)

    def test_upstream_failure_records_pending_manual_fallback_without_mutating_valid_fact(self) -> None:
        valid = VerificationCheck.objects.create(
            provider=self.provider,
            kind="business_identity",
            status=VerificationCheck.Status.VERIFIED,
            source_url="https://example.invalid/prior-snapshot",
            evidence_metadata={"source_snapshot": {"businessId": self.provider.y_tunnus}},
            checked_by=self.staff,
        )
        adapter = YtjPrhAdapter(
            transport=FakeTransport(
                [
                    TransportResponse(503, {}),
                    TransportResponse(503, {}),
                    TransportResponse(503, {}),
                ]
            ),
            sleep=lambda _: None,
        )

        fallback = run_ytj_business_identity_check(
            provider_id=self.provider.pk,
            actor=self.staff,
            adapter=adapter,
        )

        valid.refresh_from_db()
        self.assertEqual(valid.status, VerificationCheck.Status.VERIFIED)
        self.assertEqual(fallback.status, VerificationCheck.Status.PENDING)
        self.assertTrue(fallback.evidence_metadata["manual_fallback_required"])
        self.assertEqual(fallback.evidence_metadata["attempts"], 3)
