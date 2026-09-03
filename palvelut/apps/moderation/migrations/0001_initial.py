from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("providers", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ModerationCase",
            fields=[
                ("id", models.UUIDField(db_default=models.Func(function="uuidv7"), editable=False, primary_key=True, serialize=False)),
                ("reason", models.CharField(max_length=120)),
                ("status", models.CharField(choices=[("open", "Open"), ("resolved", "Resolved"), ("dismissed", "Dismissed")], default="open", max_length=16)),
                ("opened_at", models.DateTimeField(auto_now_add=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("opened_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="opened_moderation_cases", to=settings.AUTH_USER_MODEL)),
                ("provider", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="moderation_cases", to="providers.provider")),
            ],
            options={"ordering": ("-opened_at", "-id")},
        ),
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.UUIDField(db_default=models.Func(function="uuidv7"), editable=False, primary_key=True, serialize=False)),
                ("action", models.CharField(max_length=120)),
                ("metadata", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="audit_events", to=settings.AUTH_USER_MODEL)),
                ("provider", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="audit_events", to="providers.provider")),
            ],
            options={"ordering": ("-created_at", "-id")},
        ),
        migrations.CreateModel(
            name="ModerationEvent",
            fields=[
                ("id", models.UUIDField(db_default=models.Func(function="uuidv7"), editable=False, primary_key=True, serialize=False)),
                ("event_type", models.CharField(max_length=80)),
                ("note", models.TextField(blank=True)),
                ("metadata", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="moderation_events", to=settings.AUTH_USER_MODEL)),
                ("case", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="moderation.moderationcase")),
            ],
            options={"ordering": ("created_at", "id")},
        ),
    ]
