from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("moderation", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="moderationcase",
            name="kind",
            field=models.CharField(
                choices=[
                    ("provider_review", "Provider review"),
                    ("content_report", "Content report"),
                ],
                default="provider_review",
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name="moderationcase",
            name="status_token_hash",
            field=models.CharField(blank=True, db_index=True, max_length=64),
        ),
        migrations.AlterField(
            model_name="moderationcase",
            name="opened_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="opened_moderation_cases",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="moderationevent",
            name="visible_to_provider",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="moderationevent",
            name="actor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="moderation_events",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="ContentReport",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False, editable=False)),
                ("category", models.CharField(max_length=40)),
                ("details", models.TextField(max_length=2000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "case",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="content_report",
                        to="moderation.moderationcase",
                    ),
                ),
            ],
            options={"ordering": ("-created_at", "-id")},
        ),
    ]
