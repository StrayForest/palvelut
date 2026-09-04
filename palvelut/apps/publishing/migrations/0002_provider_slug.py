from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("providers", "0004_membership_requires_approved_claim"),
        ("publishing", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProviderSlug",
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
                ("slug", models.SlugField(max_length=220, unique=True)),
                ("is_current", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="slugs",
                        to="providers.provider",
                    ),
                ),
            ],
            options={"ordering": ("-is_current", "created_at", "id")},
        ),
        migrations.AddConstraint(
            model_name="providerslug",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_current", True)),
                fields=("provider",),
                name="publishing_provider_slug_one_current",
            ),
        ),
    ]
