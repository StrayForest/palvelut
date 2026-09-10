import uuid
from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from palvelut.apps.analytics.beta import (
    BETA_BOT_RULE_VERSION,
    BETA_METRIC_VERSION,
    BETA_SCHEMA_VERSION,
    BETA_SESSION_COOKIE,
    reconcile_beta_snapshot,
    signed_event_token,
)
from palvelut.apps.analytics.models import BetaFunnelEvent
from palvelut.apps.providers.models import Provider


@override_settings(ENVIRONMENT="test")
class BetaFunnelAcceptanceTests(TestCase):
    def test_collection_is_anonymous_versioned_and_bot_filtered(self):
        token = signed_event_token(BetaFunnelEvent.Kind.DISCOVERY_VIEW)
        response = self.client.get(
            reverse("beta-analytics-collect"),
            {"event": token},
            HTTP_CF_IPCOUNTRY="FI",
            HTTP_USER_AGENT="Mozilla/5.0",
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertIn(BETA_SESSION_COOKIE, response.cookies)
        event = BetaFunnelEvent.objects.get()
        self.assertEqual(event.country_code, "FI")
        self.assertEqual(event.schema_version, BETA_SCHEMA_VERSION)
        self.assertEqual(event.metric_version, BETA_METRIC_VERSION)
        self.assertEqual(event.bot_rule_version, BETA_BOT_RULE_VERSION)

        self.client.get(
            reverse("beta-analytics-collect"),
            {"event": token},
            HTTP_CF_IPCOUNTRY="FI",
            HTTP_X_PALVELUT_VERIFIED_BOT="1",
        )
        self.assertEqual(BetaFunnelEvent.objects.count(), 1)

        field_names = {field.name for field in BetaFunnelEvent._meta.fields}
        self.assertFalse(
            {"ip", "ip_address", "user_agent", "account", "user", "query"}
            & field_names
        )

    def test_search_payload_records_only_result_state_not_query_text(self):
        token = signed_event_token(
            BetaFunnelEvent.Kind.SEARCH,
            search_had_results=False,
        )
        response = self.client.get(
            reverse("beta-analytics-collect"),
            {"event": token},
            HTTP_CF_IPCOUNTRY="FI",
        )
        self.assertEqual(response.status_code, 204)
        event = BetaFunnelEvent.objects.get()
        self.assertEqual(event.kind, BetaFunnelEvent.Kind.SEARCH)
        self.assertIs(event.search_had_results, False)
        self.assertIsNone(event.provider_id)

    @override_settings(
        GOOGLE_SITE_VERIFICATION="google-proof",
        BING_SITE_VERIFICATION="bing-proof",
    )
    def test_home_exposes_search_engine_verification_without_changing_cache_contract(self):
        response = self.client.get(reverse("localized-home", kwargs={"locale": "en"}))
        self.assertContains(response, 'name="google-site-verification" content="google-proof"')
        self.assertContains(response, 'name="msvalidate.01" content="bing-proof"')
        self.assertContains(response, reverse("beta-analytics-collect"))
        self.assertIn("public", response["Cache-Control"])
        self.assertNotIn(BETA_SESSION_COOKIE, response.cookies)

    def test_reconciliation_matches_raw_events_for_frozen_versions(self):
        provider = Provider.objects.create(
            provider_type=Provider.Type.INDIVIDUAL,
            lifecycle=Provider.Lifecycle.PUBLISHED,
            claim_status=Provider.ClaimStatus.APPROVED,
            legal_name="Beta Provider",
            display_name="Beta Provider",
        )
        now = timezone.now()
        converted_session = uuid.uuid4()
        zero_session = uuid.uuid4()

        search = BetaFunnelEvent.objects.create(
            session_id=converted_session,
            kind=BetaFunnelEvent.Kind.SEARCH,
            country_code="FI",
            search_had_results=True,
            schema_version=BETA_SCHEMA_VERSION,
            metric_version=BETA_METRIC_VERSION,
            bot_rule_version=BETA_BOT_RULE_VERSION,
        )
        contact = BetaFunnelEvent.objects.create(
            session_id=converted_session,
            kind=BetaFunnelEvent.Kind.CONTACT,
            provider=provider,
            channel="email",
            country_code="FI",
            schema_version=BETA_SCHEMA_VERSION,
            metric_version=BETA_METRIC_VERSION,
            bot_rule_version=BETA_BOT_RULE_VERSION,
        )
        zero = BetaFunnelEvent.objects.create(
            session_id=zero_session,
            kind=BetaFunnelEvent.Kind.SEARCH,
            country_code="FI",
            search_had_results=False,
            schema_version=BETA_SCHEMA_VERSION,
            metric_version=BETA_METRIC_VERSION,
            bot_rule_version=BETA_BOT_RULE_VERSION,
        )
        BetaFunnelEvent.objects.filter(pk=search.pk).update(
            occurred_at=now - timedelta(minutes=3)
        )
        BetaFunnelEvent.objects.filter(pk=contact.pk).update(
            occurred_at=now - timedelta(minutes=2)
        )
        BetaFunnelEvent.objects.filter(pk=zero.pk).update(
            occurred_at=now - timedelta(minutes=1)
        )

        snapshot = reconcile_beta_snapshot(window_end=now)
        self.assertEqual(snapshot.raw_event_count, 3)
        self.assertEqual(snapshot.finland_discovery_sessions, 2)
        self.assertEqual(snapshot.search_sessions, 2)
        self.assertEqual(snapshot.search_sessions_with_contact, 1)
        self.assertEqual(snapshot.search_events, 2)
        self.assertEqual(snapshot.zero_result_searches, 1)
        self.assertEqual(snapshot.contact_conversion_basis_points, 5000)
        self.assertEqual(snapshot.zero_result_basis_points, 5000)
        self.assertEqual(len(snapshot.source_checksum), 64)
