from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("providers", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="provider",
            constraint=models.CheckConstraint(
                condition=models.Q(provider_type__in=("individual", "business")),
                name="providers_provider_type_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="provider",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    lifecycle__in=(
                        "unclaimed",
                        "draft",
                        "pending",
                        "published",
                        "changes_requested",
                        "suspended",
                        "archived",
                    )
                ),
                name="providers_provider_lifecycle_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="provider",
            constraint=models.UniqueConstraint(
                fields=("y_tunnus",),
                condition=~models.Q(y_tunnus=""),
                name="providers_provider_y_tunnus_unique_nonblank",
            ),
        ),
        migrations.AddConstraint(
            model_name="providermembership",
            constraint=models.CheckConstraint(
                condition=models.Q(role__in=("owner", "editor")),
                name="providers_membership_role_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="providermembership",
            constraint=models.UniqueConstraint(
                fields=("provider", "account"),
                name="providers_membership_provider_account_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="providermembership",
            constraint=models.UniqueConstraint(
                fields=("provider",),
                condition=models.Q(role="owner", is_active=True),
                name="providers_membership_one_active_owner",
            ),
        ),
        migrations.AddConstraint(
            model_name="providerservice",
            constraint=models.UniqueConstraint(
                fields=("provider", "category", "title"),
                name="providers_service_provider_category_title_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="servicearea",
            constraint=models.CheckConstraint(
                condition=models.Q(mode__in=("onsite", "travel", "remote")),
                name="providers_service_area_mode_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="servicearea",
            constraint=models.UniqueConstraint(
                fields=("provider", "municipality", "mode"),
                name="providers_service_area_provider_municipality_mode_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="providerlanguage",
            constraint=models.UniqueConstraint(
                fields=("provider", "language"),
                name="providers_language_provider_language_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="contactchannel",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    kind__in=(
                        "phone",
                        "email",
                        "website",
                        "booking",
                        "telegram",
                        "whatsapp",
                    )
                ),
                name="providers_contact_kind_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="contactchannel",
            constraint=models.UniqueConstraint(
                fields=("provider", "kind", "value"),
                name="providers_contact_provider_kind_value_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="mediaasset",
            constraint=models.UniqueConstraint(
                fields=("provider", "storage_key"),
                name="providers_media_provider_storage_key_unique",
            ),
        ),
    ]
