import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("analytics", "0002_provider_impressions_profile_views"),
        ("providers", "0006_provider_access_audit"),
    ]

    operations = [
        migrations.CreateModel(
            name="BetaDecisionSnapshot",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_default=models.Func(function="uuidv7"),
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("window_start", models.DateTimeField()),
                ("window_end", models.DateTimeField()),
                ("schema_version", models.CharField(max_length=32)),
                ("metric_version", models.CharField(max_length=32)),
                ("bot_rule_version", models.CharField(max_length=32)),
                ("raw_event_count", models.PositiveIntegerField()),
                ("finland_discovery_sessions", models.PositiveIntegerField()),
                ("search_sessions", models.PositiveIntegerField()),
                ("search_sessions_with_contact", models.PositiveIntegerField()),
                ("search_events", models.PositiveIntegerField()),
                ("zero_result_searches", models.PositiveIntegerField()),
                ("contact_conversion_basis_points", models.PositiveIntegerField()),
                ("zero_result_basis_points", models.PositiveIntegerField()),
                ("source_checksum", models.CharField(max_length=64)),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ("-generated_at", "-id")},
        ),
        migrations.CreateModel(
            name="BetaFunnelEvent",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_default=models.Func(function="uuidv7"),
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("session_id", models.UUIDField()),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("discovery_view", "Discovery view"),
                            ("search", "Search"),
                            ("contact", "Contact"),
                        ],
                        max_length=24,
                    ),
                ),
                ("channel", models.CharField(blank=True, default="", max_length=16)),
                ("country_code", models.CharField(max_length=2)),
                ("search_had_results", models.BooleanField(blank=True, null=True)),
                ("schema_version", models.CharField(max_length=32)),
                ("metric_version", models.CharField(max_length=32)),
                ("bot_rule_version", models.CharField(max_length=32)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                (
                    "provider",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="beta_funnel_events",
                        to="providers.provider",
                    ),
                ),
            ],
            options={
                "ordering": ("occurred_at", "id"),
                "indexes": [
                    models.Index(
                        fields=["occurred_at", "country_code"],
                        name="beta_evt_time_country",
                    ),
                    models.Index(
                        fields=["session_id", "occurred_at"],
                        name="beta_evt_session_time",
                    ),
                    models.Index(
                        fields=["kind", "occurred_at"],
                        name="beta_evt_kind_time",
                    ),
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            ("kind__in", ("discovery_view", "search", "contact"))
                        ),
                        name="beta_funnel_event_kind_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("country_code__regex", "^[A-Z]{2}$")),
                        name="beta_funnel_country_code_shape",
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(
                                ("channel", ""),
                                ("kind", "search"),
                                ("provider__isnull", True),
                                ("search_had_results__isnull", False),
                            )
                            | models.Q(
                                ("channel__gt", ""),
                                ("kind", "contact"),
                                ("provider__isnull", False),
                                ("search_had_results__isnull", True),
                            )
                            | models.Q(
                                ("channel", ""),
                                ("kind", "discovery_view"),
                                ("search_had_results__isnull", True),
                            )
                        ),
                        name="beta_funnel_event_payload_matches_kind",
                    ),
                ],
            },
        ),
    ]
