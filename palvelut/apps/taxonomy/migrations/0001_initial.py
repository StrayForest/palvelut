from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Country",
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
                ("code", models.CharField(max_length=2, unique=True)),
                ("name", models.CharField(max_length=120)),
            ],
            options={
                "ordering": ("code",),
            },
        ),
        migrations.CreateModel(
            name="Region",
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
                ("code", models.CharField(max_length=32)),
                ("name", models.CharField(max_length=120)),
                (
                    "country",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="regions",
                        to="taxonomy.country",
                    ),
                ),
            ],
            options={
                "ordering": ("country_id", "code"),
            },
        ),
        migrations.CreateModel(
            name="Municipality",
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
                ("code", models.CharField(max_length=16)),
                ("name", models.CharField(max_length=120)),
                (
                    "region",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="municipalities",
                        to="taxonomy.region",
                    ),
                ),
            ],
            options={
                "ordering": ("region_id", "code"),
            },
        ),
        migrations.AddConstraint(
            model_name="country",
            constraint=models.CheckConstraint(
                condition=models.Q(("code__regex", "^[A-Z]{2}$")),
                name="taxonomy_country_code_iso_alpha2",
            ),
        ),
        migrations.AddConstraint(
            model_name="region",
            constraint=models.UniqueConstraint(
                fields=("country", "code"),
                name="taxonomy_region_country_code_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="municipality",
            constraint=models.UniqueConstraint(
                fields=("region", "code"),
                name="taxonomy_municipality_region_code_unique",
            ),
        ),
    ]
