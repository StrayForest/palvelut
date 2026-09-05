from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("providers", "0004_membership_requires_approved_claim"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProviderInvitation",
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
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("accepted", "Accepted"),
                            ("revoked", "Revoked"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "invited_account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="provider_invitations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "invited_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sent_provider_invitations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "provider",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitations",
                        to="providers.provider",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("role__in", ("owner", "editor"))),
                        name="providers_invitation_role_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("status__in", ("pending", "accepted", "revoked"))),
                        name="providers_invitation_status_valid",
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(("status", "pending")),
                        fields=("provider", "invited_account"),
                        name="providers_invitation_one_pending_per_account",
                    ),
                ]
            },
        )
    ]
