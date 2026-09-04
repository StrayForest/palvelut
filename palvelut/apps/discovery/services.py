from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence
from typing import Any

from django.db import transaction

from palvelut.apps.discovery.models import PublicProviderDocument
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision


def _search_values(value: Any) -> list[str]:
    if isinstance(value, str):
        normalized = unicodedata.normalize("NFKC", value).casefold().strip()
        return [normalized] if normalized else []
    if isinstance(value, Mapping):
        values: list[str] = []
        for key in sorted(value, key=str):
            values.extend(_search_values(value[key]))
        return values
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        values = []
        for item in value:
            values.extend(_search_values(item))
        return values
    return []


@transaction.atomic
def refresh_public_provider_document(*, provider_id: object) -> PublicProviderDocument | None:
    """Regenerate public state strictly from the latest approved profile revision."""

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

    payload = revision.payload
    document, _ = PublicProviderDocument.objects.update_or_create(
        provider=provider,
        defaults={
            "revision": revision,
            "payload": payload,
            "search_text": " ".join(_search_values(payload)),
        },
    )
    return document
