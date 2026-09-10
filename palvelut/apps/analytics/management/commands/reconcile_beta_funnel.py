import json

from django.core.management.base import BaseCommand

from palvelut.apps.analytics.beta import reconcile_beta_snapshot
from palvelut.observability import set_metric


class Command(BaseCommand):
    help = "Reconcile the frozen P6 beta funnel and refresh dashboard gauges."

    def handle(self, *args, **options):
        snapshot = reconcile_beta_snapshot()
        set_metric("palvelut_beta_raw_events", snapshot.raw_event_count)
        set_metric(
            "palvelut_beta_finland_discovery_sessions",
            snapshot.finland_discovery_sessions,
        )
        set_metric("palvelut_beta_search_sessions", snapshot.search_sessions)
        set_metric(
            "palvelut_beta_contact_conversion_ratio",
            snapshot.contact_conversion_basis_points / 10_000,
        )
        set_metric(
            "palvelut_beta_zero_result_ratio",
            snapshot.zero_result_basis_points / 10_000,
        )
        self.stdout.write(
            json.dumps(
                {
                    "snapshot_id": str(snapshot.id),
                    "window_start": snapshot.window_start.isoformat(),
                    "window_end": snapshot.window_end.isoformat(),
                    "schema_version": snapshot.schema_version,
                    "metric_version": snapshot.metric_version,
                    "bot_rule_version": snapshot.bot_rule_version,
                    "raw_event_count": snapshot.raw_event_count,
                    "finland_discovery_sessions": snapshot.finland_discovery_sessions,
                    "search_sessions": snapshot.search_sessions,
                    "search_sessions_with_contact": snapshot.search_sessions_with_contact,
                    "search_events": snapshot.search_events,
                    "zero_result_searches": snapshot.zero_result_searches,
                    "contact_conversion_ratio": snapshot.contact_conversion_basis_points
                    / 10_000,
                    "zero_result_ratio": snapshot.zero_result_basis_points / 10_000,
                    "source_checksum": snapshot.source_checksum,
                },
                sort_keys=True,
            )
        )
