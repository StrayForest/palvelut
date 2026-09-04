import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("providers", "0003_provider_claim_state"),
        ("publishing", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PublicProviderDocument",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_default=models.expressions.RawSQL("uuidv7()", []),
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("payload", models.JSONField(default=dict)),
                ("generated_at", models.DateTimeField(auto_now=True)),
                (
                    "provider",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="public_document",
                        to="providers.provider",
                    ),
                ),
                (
                    "revision",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="public_document",
                        to="publishing.profilerevision",
                    ),
                ),
            ],
            options={"ordering": ("provider_id",)},
        ),
    ]
