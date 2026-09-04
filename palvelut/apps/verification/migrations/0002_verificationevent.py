from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("verification", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="VerificationEvent",
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
                    "previous_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("verified", "Verified"),
                            ("rejected", "Rejected"),
                            ("expired", "Expired"),
                        ],
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("verified", "Verified"),
                            ("rejected", "Rejected"),
                            ("expired", "Expired"),
                        ],
                        max_length=16,
                    ),
                ),
                ("metadata", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="verification_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "check",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="verification.verificationcheck",
                    ),
                ),
            ],
            options={"ordering": ("created_at", "id")},
        ),
    ]
