from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("moderation", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="moderationcase",
            name="closed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="closed_moderation_cases",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name="moderationcase",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(
                        ("closed_at__isnull", True),
                        ("closed_by__isnull", True),
                        ("status", "open"),
                    )
                    | models.Q(
                        ("closed_at__isnull", False),
                        ("closed_by__isnull", False),
                        ("status__in", ("resolved", "dismissed")),
                    )
                ),
                name="moderation_case_closure_has_actor_and_timestamp",
            ),
        ),
    ]
