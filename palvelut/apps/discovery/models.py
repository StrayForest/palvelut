from django.db import models

from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision
from palvelut.apps.taxonomy.models import UuidV7Model


class PublicProviderDocument(UuidV7Model):
    provider = models.OneToOneField(
        Provider,
        on_delete=models.CASCADE,
        related_name="public_document",
    )
    revision = models.OneToOneField(
        ProfileRevision,
        on_delete=models.PROTECT,
        related_name="public_document",
    )
    payload = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("provider_id",)
