from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("providers", "0005_provider_invitation"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProviderAccessAudit",
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
                ("target_provider_id", models.UUIDField()),
                ("method", models.CharField(max_length=8)),
                ("path", models.CharField(max_length=500)),
                (
                    "outcome",
                    models.CharField(
                        choices=[("denied", "Denied")],
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="provider_access_audits",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at", "-id"),
                "indexes": [
                    models.Index(
                        fields=["target_provider_id", "created_at"],
                        name="prov_access_target_created_idx",
                    )
                ],
            },
        ),
    ]
