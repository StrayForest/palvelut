from django.core.exceptions import ValidationError
from django.db import transaction

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision


@transaction.atomic
def rebuild_provider_read_document(*, provider_id: object) -> ProviderReadDocument:
    provider = Provider.objects.select_for_update().get(pk=provider_id)
    if provider.lifecycle != Provider.Lifecycle.PUBLISHED:
        raise ValidationError(
            "Only published providers can have a public read document"
        )

    revision = (
        ProfileRevision.objects.select_for_update()
        .filter(provider=provider, status=ProfileRevision.Status.APPROVED)
        .order_by("-reviewed_at", "-created_at", "-id")
        .first()
    )
    if revision is None:
        raise ValidationError("Public read document requires an approved revision")

    document, _ = ProviderReadDocument.objects.update_or_create(
        provider=provider,
        defaults={
            "source_revision": revision,
            "document": revision.payload,
        },
    )
    return document


@transaction.atomic
def remove_provider_read_document(*, provider_id: object) -> None:
    ProviderReadDocument.objects.filter(provider_id=provider_id).delete()
