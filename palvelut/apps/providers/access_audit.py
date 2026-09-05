from django.conf import settings
from django.db import models

from palvelut.apps.taxonomy.models import UuidV7Model


class ProviderAccessAudit(UuidV7Model):
    class Outcome(models.TextChoices):
        DENIED = "denied", "Denied"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="provider_access_audits",
    )
    target_provider_id = models.UUIDField()
    method = models.CharField(max_length=8)
    path = models.CharField(max_length=500)
    outcome = models.CharField(max_length=16, choices=Outcome.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = (
            models.Index(
                fields=("target_provider_id", "created_at"),
                name="provider_access_target_created_idx",
            ),
        )


def audit_cross_provider_denial(*, actor, provider_id, method: str, path: str) -> None:
    ProviderAccessAudit.objects.create(
        actor=actor,
        target_provider_id=provider_id,
        method=method[:8],
        path=path[:500],
        outcome=ProviderAccessAudit.Outcome.DENIED,
    )
