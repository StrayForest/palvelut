from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction

from palvelut.apps.providers.image_safety import sanitize_image
from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.publishing.models import ProfileRevision

PROFILE_FIELDS = ("provider_type", "legal_name", "display_name", "y_tunnus")
STRUCTURED_FIELDS = ("contacts", "services", "service_areas", "languages", "media")
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def provider_for_account(*, provider_id: object, account) -> Provider:
    membership = (
        ProviderMembership.objects.select_related("provider")
        .filter(provider_id=provider_id, account=account, is_active=True)
        .first()
    )
    if membership is None:
        raise PermissionDenied("provider membership required")
    return membership.provider


def _provider_payload(provider: Provider) -> dict[str, Any]:
    return {
        **{field: getattr(provider, field) for field in PROFILE_FIELDS},
        "contacts": [
            {
                "kind": row.kind,
                "value": row.value,
                "label": row.label,
                "is_public": row.is_public,
                "sort_order": row.sort_order,
            }
            for row in provider.contacts.order_by("sort_order", "id")
        ],
        "services": [
            {
                "category_id": str(row.category_id),
                "title": row.title,
                "description": row.description,
                "price_text": row.price_text,
                "is_active": row.is_active,
            }
            for row in provider.services.order_by("id")
        ],
        "service_areas": [
            {"municipality_id": str(row.municipality_id), "mode": row.mode}
            for row in provider.service_areas.order_by("id")
        ],
        "languages": [
            {"language_id": str(row.language_id), "declared": row.declared}
            for row in provider.languages.order_by("id")
        ],
        "media": [
            {
                "storage_key": row.storage_key,
                "content_type": row.content_type,
                "alt_text": row.alt_text,
                "width": row.width,
                "height": row.height,
                "sort_order": row.sort_order,
            }
            for row in provider.media_assets.order_by("sort_order", "id")
        ],
    }


def approved_payload(provider: Provider) -> dict[str, Any]:
    revision = (
        ProfileRevision.objects.filter(
            provider=provider,
            status=ProfileRevision.Status.APPROVED,
        )
        .order_by("-reviewed_at", "-created_at", "-id")
        .first()
    )
    if revision is not None:
        payload = _provider_payload(provider)
        payload.update(dict(revision.payload))
        for field in STRUCTURED_FIELDS:
            payload.setdefault(field, [])
        return payload
    return _provider_payload(provider)


def editable_revision(*, provider: Provider, account) -> ProfileRevision:
    revision = (
        ProfileRevision.objects.filter(
            provider=provider,
            created_by=account,
            status__in=(
                ProfileRevision.Status.DRAFT,
                ProfileRevision.Status.CHANGES_REQUESTED,
            ),
        )
        .order_by("-created_at", "-id")
        .first()
    )
    if revision is not None:
        return revision
    return ProfileRevision.objects.create(
        provider=provider,
        created_by=account,
        status=ProfileRevision.Status.DRAFT,
        payload=approved_payload(provider),
    )


@transaction.atomic
def autosave_revision(
    *, provider_id: object, account, payload: dict[str, Any]
) -> ProfileRevision:
    provider = provider_for_account(provider_id=provider_id, account=account)
    provider = Provider.objects.select_for_update().get(pk=provider.pk)
    revision = editable_revision(provider=provider, account=account)
    if revision.status == ProfileRevision.Status.CHANGES_REQUESTED:
        revision.status = ProfileRevision.Status.DRAFT
    current = dict(revision.payload)
    current.update({field: str(payload.get(field, "")) for field in PROFILE_FIELDS})
    for field in ("contacts", "services", "service_areas", "languages"):
        current[field] = list(payload.get(field, []))
    current.setdefault("media", [])
    revision.payload = current
    revision.save(update_fields=("payload", "status"))
    return revision


@transaction.atomic
def stage_media_upload(
    *,
    provider_id: object,
    account,
    uploaded_file,
    alt_text: str = "",
) -> ProfileRevision:
    provider = provider_for_account(provider_id=provider_id, account=account)
    provider = Provider.objects.select_for_update().get(pk=provider.pk)
    content_type = str(getattr(uploaded_file, "content_type", ""))
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError("unsupported image content type")
    if (
        int(getattr(uploaded_file, "size", 0)) <= 0
        or uploaded_file.size > MAX_IMAGE_BYTES
    ):
        raise ValidationError("image must be between 1 byte and 10 MiB")
    expected_suffix = ALLOWED_IMAGE_TYPES[content_type]
    original_suffix = Path(str(getattr(uploaded_file, "name", ""))).suffix.lower()
    allowed_suffixes = {expected_suffix}
    if expected_suffix == ".jpg":
        allowed_suffixes.add(".jpeg")
    if original_suffix not in allowed_suffixes:
        raise ValidationError("image extension does not match content type")

    sanitized = sanitize_image(
        payload=uploaded_file.read(),
        declared_content_type=content_type,
    )
    revision = editable_revision(provider=provider, account=account)
    key = f"provider-media/staging/{provider.pk}/{uuid4().hex}{sanitized.extension}"
    stored_key = default_storage.save(key, ContentFile(sanitized.data))
    payload = dict(revision.payload)
    media = list(payload.get("media", []))
    media.append(
        {
            "storage_key": stored_key,
            "content_type": sanitized.content_type,
            "alt_text": alt_text.strip()[:240],
            "width": sanitized.width,
            "height": sanitized.height,
            "sort_order": len(media),
        }
    )
    payload["media"] = media
    revision.payload = payload
    if revision.status == ProfileRevision.Status.CHANGES_REQUESTED:
        revision.status = ProfileRevision.Status.DRAFT
    revision.save(update_fields=("payload", "status"))
    return revision


@transaction.atomic
def submit_revision(*, provider_id: object, account) -> ProfileRevision:
    provider = provider_for_account(provider_id=provider_id, account=account)
    provider = Provider.objects.select_for_update().get(pk=provider.pk)
    revision = editable_revision(provider=provider, account=account)
    missing = [
        field
        for field in ("provider_type", "legal_name", "display_name")
        if not revision.payload.get(field)
    ]
    if missing:
        raise ValidationError(f"missing required profile fields: {', '.join(missing)}")
    revision.status = ProfileRevision.Status.PENDING
    revision.save(update_fields=("status",))
    if provider.lifecycle != Provider.Lifecycle.PUBLISHED:
        provider.lifecycle = Provider.Lifecycle.PENDING
        provider.save(update_fields=("lifecycle", "updated_at"))
    return revision
