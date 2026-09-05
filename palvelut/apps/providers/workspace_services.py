from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.publishing.models import ProfileRevision

PROFILE_FIELDS = ("provider_type", "legal_name", "display_name", "y_tunnus")


def provider_for_account(*, provider_id: object, account) -> Provider:
    membership = (
        ProviderMembership.objects.select_related("provider")
        .filter(provider_id=provider_id, account=account, is_active=True)
        .first()
    )
    if membership is None:
        raise PermissionDenied("provider membership required")
    return membership.provider


def approved_payload(provider: Provider) -> dict[str, str]:
    revision = (
        ProfileRevision.objects.filter(
            provider=provider,
            status=ProfileRevision.Status.APPROVED,
        )
        .order_by("-reviewed_at", "-created_at", "-id")
        .first()
    )
    if revision is not None:
        return dict(revision.payload)
    return {field: getattr(provider, field) for field in PROFILE_FIELDS}


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
def autosave_revision(*, provider_id: object, account, payload: dict) -> ProfileRevision:
    provider = provider_for_account(provider_id=provider_id, account=account)
    provider = Provider.objects.select_for_update().get(pk=provider.pk)
    revision = editable_revision(provider=provider, account=account)
    if revision.status == ProfileRevision.Status.CHANGES_REQUESTED:
        revision.status = ProfileRevision.Status.DRAFT
    revision.payload = {field: str(payload.get(field, "")) for field in PROFILE_FIELDS}
    revision.save(update_fields=("payload", "status"))
    return revision


@transaction.atomic
def submit_revision(*, provider_id: object, account) -> ProfileRevision:
    provider = provider_for_account(provider_id=provider_id, account=account)
    provider = Provider.objects.select_for_update().get(pk=provider.pk)
    revision = editable_revision(provider=provider, account=account)
    missing = [field for field in ("provider_type", "legal_name", "display_name") if not revision.payload.get(field)]
    if missing:
        raise ValidationError(f"missing required profile fields: {', '.join(missing)}")
    revision.status = ProfileRevision.Status.PENDING
    revision.save(update_fields=("status",))
    if provider.lifecycle != Provider.Lifecycle.PUBLISHED:
        provider.lifecycle = Provider.Lifecycle.PENDING
        provider.save(update_fields=("lifecycle", "updated_at"))
    return revision
