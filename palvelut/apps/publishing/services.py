from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from palvelut.apps.moderation.services import record_audit
from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.publishing.models import ProfileRevision


def revision_diff(revision: ProfileRevision) -> dict[str, dict[str, Any]]:
    previous = (
        ProfileRevision.objects.filter(
            provider=revision.provider,
            status=ProfileRevision.Status.APPROVED,
        )
        .exclude(pk=revision.pk)
        .order_by("-reviewed_at", "-created_at", "-id")
        .first()
    )
    before = previous.payload if previous is not None else {}
    after = revision.payload
    keys = sorted(set(before) | set(after))
    return {
        key: {"before": before.get(key), "after": after.get(key)}
        for key in keys
        if before.get(key) != after.get(key)
    }


@transaction.atomic
def approve_revision(*, revision: ProfileRevision, actor: AbstractBaseUser) -> ProfileRevision:
    revision = ProfileRevision.objects.select_for_update().select_related("provider").get(pk=revision.pk)
    provider = Provider.objects.select_for_update().get(pk=revision.provider_id)

    if revision.status != ProfileRevision.Status.PENDING:
        raise ValidationError("Only pending revisions can be approved")
    if provider.lifecycle == Provider.Lifecycle.UNCLAIMED:
        raise ValidationError("Unclaimed providers cannot publish")
    if not ProviderMembership.objects.filter(
        provider=provider,
        role=ProviderMembership.Role.OWNER,
        is_active=True,
    ).exists():
        raise ValidationError("Provider must have an active owner before publication")

    ProfileRevision.objects.filter(
        provider=provider,
        status=ProfileRevision.Status.APPROVED,
    ).exclude(pk=revision.pk).update(status=ProfileRevision.Status.SUPERSEDED)

    now = timezone.now()
    revision.status = ProfileRevision.Status.APPROVED
    revision.reviewed_at = now
    revision.save(update_fields=("status", "reviewed_at"))

    previous = provider.lifecycle
    provider.lifecycle = Provider.Lifecycle.PUBLISHED
    provider.save(update_fields=("lifecycle", "updated_at"))
    record_audit(
        actor=actor,
        provider=provider,
        action="revision.approved",
        metadata={"revision_id": str(revision.pk), "provider_from": previous},
    )
    return revision


@transaction.atomic
def request_revision_changes(*, revision: ProfileRevision, actor: AbstractBaseUser) -> ProfileRevision:
    revision = ProfileRevision.objects.select_for_update().select_related("provider").get(pk=revision.pk)
    provider = Provider.objects.select_for_update().get(pk=revision.provider_id)
    if revision.status != ProfileRevision.Status.PENDING:
        raise ValidationError("Only pending revisions can request changes")

    revision.status = ProfileRevision.Status.CHANGES_REQUESTED
    revision.reviewed_at = timezone.now()
    revision.save(update_fields=("status", "reviewed_at"))

    previous = provider.lifecycle
    provider.lifecycle = Provider.Lifecycle.CHANGES_REQUESTED
    provider.save(update_fields=("lifecycle", "updated_at"))
    record_audit(
        actor=actor,
        provider=provider,
        action="revision.changes_requested",
        metadata={"revision_id": str(revision.pk), "provider_from": previous},
    )
    return revision
