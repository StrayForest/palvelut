import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("providers", "0004_membership_requires_approved_claim"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnalyticsEvent",
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
                (
                    "kind",
                    models.CharField(
                        choices=[("contact_click", "Contact click")], max_length=32
                    ),
                ),
                ("channel", models.CharField(max_length=16)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analytics_events",
                        to="providers.provider",
                    ),
                ),
            ],
            options={
                "ordering": ("occurred_at", "id"),
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("kind", "contact_click")),
                        name="analytics_event_kind_valid",
                    )
                ],
            },
        ),
    ]
