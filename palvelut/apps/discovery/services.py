from __future__ import annotations

from django.db import transaction

from palvelut.apps.discovery.models import PublicProviderDocument
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision


@transaction.atomic
def sync_public_provider_document(
    *, provider_id: object
) -> PublicProviderDocument | None:
    provider = Provider.objects.select_for_update().get(pk=provider_id)

    if (
        provider.lifecycle != Provider.Lifecycle.PUBLISHED
        or provider.claim_status != Provider.ClaimStatus.APPROVED
    ):
        PublicProviderDocument.objects.filter(provider=provider).delete()
        return None

    revision = (
        ProfileRevision.objects.filter(
            provider=provider,
            status=ProfileRevision.Status.APPROVED,
        )
        .order_by("-reviewed_at", "-created_at", "-id")
        .first()
    )
    if revision is None:
        PublicProviderDocument.objects.filter(provider=provider).delete()
        return None

    document, _ = PublicProviderDocument.objects.update_or_create(
        provider=provider,
        defaults={
            "revision": revision,
            "payload": revision.payload,
        },
    )
    return document
