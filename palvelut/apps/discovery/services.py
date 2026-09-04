from __future__ import annotations

import json
from typing import Any

from django.core.exceptions import ValidationError

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision


def _collect_searchable_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, dict):
        parts: list[str] = []
        for key in sorted(value):
            parts.extend(_collect_searchable_strings(value[key]))
        return parts
    if isinstance(value, list):
        parts = []
        for item in value:
            parts.extend(_collect_searchable_strings(item))
        return parts
    return []


def publish_approved_revision(*, revision: ProfileRevision) -> ProviderReadDocument:
    if (
        revision.status != ProfileRevision.Status.APPROVED
        or revision.reviewed_at is None
    ):
        raise ValidationError("Public read documents require an approved revision")
    if revision.provider.lifecycle != Provider.Lifecycle.PUBLISHED:
        raise ValidationError("Public read documents require a published provider")

    document = json.loads(json.dumps(revision.payload))
    searchable_text = " ".join(_collect_searchable_strings(document))
    read_document, _ = ProviderReadDocument.objects.update_or_create(
        provider=revision.provider,
        defaults={
            "source_revision": revision,
            "document": document,
            "searchable_text": searchable_text,
            "published_at": revision.reviewed_at,
        },
    )
    return read_document


def remove_public_read_document(*, provider: Provider) -> None:
    ProviderReadDocument.objects.filter(provider=provider).delete()
