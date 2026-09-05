from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("analytics", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="analyticsevent",
            name="kind",
            field=models.CharField(
                choices=[
                    ("impression", "Impression"),
                    ("profile_view", "Profile view"),
                    ("contact_click", "Contact click"),
                ],
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="analyticsevent",
            name="channel",
            field=models.CharField(blank=True, default="", max_length=16),
        ),
        migrations.RemoveConstraint(
            model_name="analyticsevent",
            name="analytics_event_kind_valid",
        ),
        migrations.AddConstraint(
            model_name="analyticsevent",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    kind__in=("impression", "profile_view", "contact_click")
                ),
                name="analytics_event_kind_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="analyticsevent",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(kind="contact_click", channel__gt="")
                    | models.Q(kind__in=("impression", "profile_view"), channel="")
                ),
                name="analytics_event_channel_matches_kind",
            ),
        ),
    ]
