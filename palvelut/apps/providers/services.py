from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.db import transaction

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import (
    ContactChannel,
    MediaAsset,
    Provider,
    ProviderLanguage,
    ProviderMembership,
    ProviderService,
    ServiceArea,
)


def _require_staff(actor: AbstractBaseUser) -> None:
    if not getattr(actor, "is_staff", False):
        raise ValidationError("Staff access is required.")


@transaction.atomic
def import_unclaimed_provider(
    *,
    actor: AbstractBaseUser,
    data: Mapping[str, Any],
) -> Provider:
    """Idempotently import a non-public provider record.

    Y-tunnus is the stable import key. Imported records are always unclaimed and receive
    no membership, so they cannot become public until the claim flow is approved.
    """

    _require_staff(actor)
    y_tunnus = str(data.get("y_tunnus", "")).strip()
    if not y_tunnus:
        raise ValidationError("Imported providers require y_tunnus for idempotency.")

    defaults = {
        "provider_type": data.get("provider_type", Provider.Type.BUSINESS),
        "legal_name": str(data.get("legal_name", "")).strip(),
        "display_name": str(data.get("display_name", "")).strip(),
        "lifecycle": Provider.Lifecycle.UNCLAIMED,
        "claim_status": Provider.ClaimStatus.UNCLAIMED,
        "claim_evidence": {},
    }
    if not defaults["legal_name"] or not defaults["display_name"]:
        raise ValidationError("legal_name and display_name are required.")

    provider, created = Provider.objects.select_for_update().get_or_create(
        y_tunnus=y_tunnus,
        defaults=defaults,
    )
    if not created:
        changed: list[str] = []
        for field in ("provider_type", "legal_name", "display_name"):
            value = defaults[field]
            if getattr(provider, field) != value:
                setattr(provider, field, value)
                changed.append(field)
        if provider.lifecycle == Provider.Lifecycle.UNCLAIMED and changed:
            provider.save(update_fields=[*changed, "updated_at"])

    AuditEvent.objects.create(
        provider=provider,
        actor=actor,
        action="provider.imported" if created else "provider.import_refreshed",
        metadata={"y_tunnus": y_tunnus},
    )
    return provider


def _move_unique_rows(
    *,
    model,
    source: Provider,
    target: Provider,
    unique_fields: tuple[str, ...],
) -> None:
    for row in model.objects.select_for_update().filter(provider=source):
        lookup = {field: getattr(row, field) for field in unique_fields}
        if model.objects.filter(provider=target, **lookup).exists():
            row.delete()
        else:
            row.provider = target
            row.save(update_fields=["provider"])


@transaction.atomic
def merge_duplicate_providers(
    *,
    actor: AbstractBaseUser,
    target_id,
    source_id,
) -> Provider:
    """Merge one duplicate into the canonical target without deleting audit history."""

    _require_staff(actor)
    if target_id == source_id:
        raise ValidationError("Target and source must be different providers.")

    providers = {
        provider.pk: provider
        for provider in Provider.objects.select_for_update().filter(
            pk__in=(target_id, source_id)
        )
    }
    if len(providers) != 2:
        raise ValidationError("Both providers must exist.")
    target = providers[target_id]
    source = providers[source_id]

    if target.y_tunnus and source.y_tunnus and target.y_tunnus != source.y_tunnus:
        raise ValidationError(
            "Providers with different Y-tunnus values cannot be merged."
        )
    if not target.y_tunnus and source.y_tunnus:
        target.y_tunnus = source.y_tunnus
        source.y_tunnus = ""
        source.save(update_fields=["y_tunnus", "updated_at"])
        target.save(update_fields=["y_tunnus", "updated_at"])

    _move_unique_rows(
        model=ProviderService,
        source=source,
        target=target,
        unique_fields=("category_id", "title"),
    )
    _move_unique_rows(
        model=ServiceArea,
        source=source,
        target=target,
        unique_fields=("municipality_id", "mode"),
    )
    _move_unique_rows(
        model=ProviderLanguage,
        source=source,
        target=target,
        unique_fields=("language_id",),
    )
    _move_unique_rows(
        model=ContactChannel,
        source=source,
        target=target,
        unique_fields=("kind", "value"),
    )
    _move_unique_rows(
        model=MediaAsset,
        source=source,
        target=target,
        unique_fields=("storage_key",),
    )

    for membership in ProviderMembership.objects.select_for_update().filter(
        provider=source
    ):
        existing = ProviderMembership.objects.filter(
            provider=target,
            account=membership.account,
        ).first()
        if existing:
            membership.delete()
        elif (
            membership.role == ProviderMembership.Role.OWNER
            and ProviderMembership.objects.filter(
                provider=target,
                role=ProviderMembership.Role.OWNER,
                is_active=True,
            ).exists()
        ):
            membership.role = ProviderMembership.Role.EDITOR
            membership.provider = target
            membership.save(update_fields=["provider", "role"])
        else:
            membership.provider = target
            membership.save(update_fields=["provider"])

    source.lifecycle = Provider.Lifecycle.ARCHIVED
    source.save(update_fields=["lifecycle", "updated_at"])
    AuditEvent.objects.create(
        provider=target,
        actor=actor,
        action="provider.duplicates_merged",
        metadata={"source_provider_id": str(source.pk)},
    )
    AuditEvent.objects.create(
        provider=source,
        actor=actor,
        action="provider.merged_into",
        metadata={"target_provider_id": str(target.pk)},
    )
    return target
