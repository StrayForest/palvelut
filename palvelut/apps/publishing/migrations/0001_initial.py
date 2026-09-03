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
            name="ProfileRevision",
            fields=[
                ("id", models.UUIDField(db_default=models.Func(function="uuidv7"), editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("pending", "Pending"), ("approved", "Approved"), ("changes_requested", "Changes requested"), ("superseded", "Superseded")], default="draft", max_length=24)),
                ("payload", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_profile_revisions", to=settings.AUTH_USER_MODEL)),
                ("provider", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="profile_revisions", to="providers.provider")),
            ],
            options={"ordering": ("-created_at", "-id")},
        ),
    ]
