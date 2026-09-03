from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("providers", "0002_domain_constraints"),
        ("verification", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProviderClaim",
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
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                (
                    "evidence_type",
                    models.CharField(
                        choices=[
                            ("registry_signatory", "Registry signatory"),
                            ("business_domain_email", "Business-domain email"),
                            ("staff_equivalent", "Staff-reviewed equivalent"),
                        ],
                        max_length=32,
                    ),
                ),
                ("evidence_metadata", models.JSONField(default=dict)),
                ("requested_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "claimant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="provider_claims",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="claims",
                        to="providers.provider",
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reviewed_provider_claims",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-requested_at", "-id"),
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(
                            ("status__in", ("pending", "approved", "rejected"))
                        ),
                        name="verification_claim_status_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            (
                                "evidence_type__in",
                                (
                                    "registry_signatory",
                                    "business_domain_email",
                                    "staff_equivalent",
                                ),
                            )
                        ),
                        name="verification_claim_evidence_type_valid",
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(("status", "pending")),
                        fields=("provider",),
                        name="verification_claim_one_pending_per_provider",
                    ),
                ],
            },
        ),
    ]
