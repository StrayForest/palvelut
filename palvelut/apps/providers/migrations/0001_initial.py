from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("taxonomy", "0002_category_language"),
    ]

    operations = [
        migrations.CreateModel(
            name="Provider",
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
                    "provider_type",
                    models.CharField(
                        choices=[
                            ("individual", "Individual"),
                            ("business", "Business"),
                        ],
                        max_length=16,
                    ),
                ),
                (
                    "lifecycle",
                    models.CharField(
                        choices=[
                            ("unclaimed", "Unclaimed"),
                            ("draft", "Draft"),
                            ("pending", "Pending"),
                            ("published", "Published"),
                            ("changes_requested", "Changes requested"),
                            ("suspended", "Suspended"),
                            ("archived", "Archived"),
                        ],
                        default="unclaimed",
                        max_length=24,
                    ),
                ),
                ("legal_name", models.CharField(max_length=200)),
                ("display_name", models.CharField(max_length=200)),
                ("y_tunnus", models.CharField(blank=True, max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("display_name", "id")},
        ),
        migrations.CreateModel(
            name="ContactChannel",
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
                    "kind",
                    models.CharField(
                        choices=[
                            ("phone", "Phone"),
                            ("email", "Email"),
                            ("website", "Website"),
                            ("booking", "Booking"),
                            ("telegram", "Telegram"),
                            ("whatsapp", "WhatsApp"),
                        ],
                        max_length=16,
                    ),
                ),
                ("value", models.CharField(max_length=500)),
                ("label", models.CharField(blank=True, max_length=80)),
                ("is_public", models.BooleanField(default=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contacts",
                        to="providers.provider",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MediaAsset",
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
                ("storage_key", models.CharField(max_length=500)),
                ("content_type", models.CharField(max_length=120)),
                ("alt_text", models.CharField(blank=True, max_length=240)),
                ("width", models.PositiveIntegerField(blank=True, null=True)),
                ("height", models.PositiveIntegerField(blank=True, null=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="media_assets",
                        to="providers.provider",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProviderLanguage",
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
                ("declared", models.BooleanField(default=True)),
                (
                    "language",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="providers",
                        to="taxonomy.language",
                    ),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="languages",
                        to="providers.provider",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProviderMembership",
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
                    "role",
                    models.CharField(
                        choices=[("owner", "Owner"), ("editor", "Editor")],
                        default="editor",
                        max_length=16,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="provider_memberships",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to="providers.provider",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProviderService",
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
                ("title", models.CharField(blank=True, max_length=160)),
                ("description", models.TextField(blank=True)),
                ("price_text", models.CharField(blank=True, max_length=160)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="provider_services",
                        to="taxonomy.category",
                    ),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="services",
                        to="providers.provider",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ServiceArea",
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
                    "mode",
                    models.CharField(
                        choices=[
                            ("onsite", "On-site"),
                            ("travel", "Travels to customer"),
                            ("remote", "Remote"),
                        ],
                        default="onsite",
                        max_length=16,
                    ),
                ),
                (
                    "municipality",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="provider_service_areas",
                        to="taxonomy.municipality",
                    ),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="service_areas",
                        to="providers.provider",
                    ),
                ),
            ],
        ),
    ]
