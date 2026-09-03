from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("taxonomy", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Category",
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
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("name", models.CharField(max_length=120)),
            ],
            options={"ordering": ("slug",)},
        ),
        migrations.CreateModel(
            name="Language",
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
                ("code", models.CharField(max_length=16, unique=True)),
                ("name", models.CharField(max_length=120)),
            ],
            options={"ordering": ("code",)},
        ),
    ]
