from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("providers", "0002_domain_constraints")]

    operations = [
        migrations.AddField(
            model_name="provider",
            name="claim_status",
            field=models.CharField(
                choices=[
                    ("unclaimed", "Unclaimed"),
                    ("pending", "Pending"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                ],
                default="unclaimed",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="provider",
            name="claim_evidence",
            field=models.JSONField(default=dict),
        ),
        migrations.AddConstraint(
            model_name="provider",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    (
                        "claim_status__in",
                        ("unclaimed", "pending", "approved", "rejected"),
                    )
                ),
                name="providers_provider_claim_status_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="provider",
            constraint=models.CheckConstraint(
                condition=(
                    ~models.Q(("lifecycle", "published"))
                    | models.Q(("claim_status", "approved"))
                ),
                name="providers_provider_published_requires_approved_claim",
            ),
        ),
    ]
