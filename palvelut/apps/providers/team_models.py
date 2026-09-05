from django.conf import settings
from django.db import models

from palvelut.apps.taxonomy.models import UuidV7Model

from .models import Provider, ProviderMembership


class ProviderInvitation(UuidV7Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REVOKED = "revoked", "Revoked"

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    invited_account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provider_invitations",
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_provider_invitations",
    )
    role = models.CharField(
        max_length=16,
        choices=ProviderMembership.Role.choices,
        default=ProviderMembership.Role.EDITOR,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = (
            models.CheckConstraint(
                condition=models.Q(role__in=("owner", "editor")),
                name="providers_invitation_role_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=("pending", "accepted", "revoked")),
                name="providers_invitation_status_valid",
            ),
            models.UniqueConstraint(
                fields=("provider", "invited_account"),
                condition=models.Q(status="pending"),
                name="providers_invitation_one_pending_per_account",
            ),
        )
