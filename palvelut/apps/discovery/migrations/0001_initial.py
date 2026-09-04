from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("providers", "0003_provider_claim_state"),
        ("publishing", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProviderReadDocument",
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
                ("document", models.JSONField(default=dict)),
                ("generated_at", models.DateTimeField(auto_now=True)),
                (
                    "provider",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="public_read_document",
                        to="providers.provider",
                    ),
                ),
                (
                    "source_revision",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="read_documents",
                        to="publishing.profilerevision",
                    ),
                ),
            ],
            options={"ordering": ("provider_id",)},
        ),
    ]
