from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("providers", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="VerificationCheck",
            fields=[
                ("id", models.UUIDField(db_default=models.Func(function="uuidv7"), editable=False, primary_key=True, serialize=False)),
                ("kind", models.CharField(max_length=80)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("verified", "Verified"), ("rejected", "Rejected"), ("expired", "Expired")], default="pending", max_length=16)),
                ("source_url", models.URLField(blank=True, max_length=500)),
                ("evidence_metadata", models.JSONField(default=dict)),
                ("checked_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("checked_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="verification_checks", to=settings.AUTH_USER_MODEL)),
                ("provider", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="verification_checks", to="providers.provider")),
            ],
            options={"ordering": ("-checked_at", "-id")},
        ),
    ]
