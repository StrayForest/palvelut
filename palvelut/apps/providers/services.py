from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.db import transaction

from palvelut.apps.moderation.services import record_audit
from palvelut.apps.providers.models import Provider, ProviderMembership


@transaction.atomic
def activate_owner_membership(*, provider: Provider, account: AbstractBaseUser) -> ProviderMembership:
    provider = Provider.objects.select_for_update().get(pk=provider.pk)
    existing_owner = (
        ProviderMembership.objects.select_for_update()
        .filter(provider=provider, role=ProviderMembership.Role.OWNER, is_active=True)
        .exclude(account=account)
        .first()
    )
    if existing_owner is not None:
        raise ValidationError("Provider already has an active owner")

    membership, _ = ProviderMembership.objects.update_or_create(
        provider=provider,
        account=account,
        defaults={"role": ProviderMembership.Role.OWNER, "is_active": True},
    )
    return membership


@transaction.atomic
def suspend_provider(*, provider: Provider, actor: AbstractBaseUser, reason: str) -> Provider:
    provider = Provider.objects.select_for_update().get(pk=provider.pk)
    if provider.lifecycle == Provider.Lifecycle.ARCHIVED:
        raise ValidationError("Archived providers cannot be suspended")
    previous = provider.lifecycle
    provider.lifecycle = Provider.Lifecycle.SUSPENDED
    provider.save(update_fields=("lifecycle", "updated_at"))
    record_audit(
        actor=actor,
        provider=provider,
        action="provider.suspended",
        metadata={"from": previous, "reason": reason},
    )
    return provider


@transaction.atomic
def merge_duplicate_pair(*, first: Provider, second: Provider, actor: AbstractBaseUser) -> Provider:
    if first.pk == second.pk:
        raise ValidationError("Select two different providers")

    provider_ids = sorted((first.pk, second.pk))
    locked = list(Provider.objects.select_for_update().filter(pk__in=provider_ids).order_by("id"))
    if len(locked) != 2:
        raise ValidationError("Both providers must exist")

    survivor, duplicate = locked
    if survivor.y_tunnus and duplicate.y_tunnus and survivor.y_tunnus != duplicate.y_tunnus:
        raise ValidationError("Providers with different Y-tunnus values cannot be merged")

    if not survivor.y_tunnus and duplicate.y_tunnus:
        survivor.y_tunnus = duplicate.y_tunnus
        survivor.save(update_fields=("y_tunnus", "updated_at"))

    duplicate.lifecycle = Provider.Lifecycle.ARCHIVED
    duplicate.save(update_fields=("lifecycle", "updated_at"))

    record_audit(
        actor=actor,
        provider=survivor,
        action="provider.duplicate_merged",
        metadata={"archived_provider_id": str(duplicate.pk)},
    )
    record_audit(
        actor=actor,
        provider=duplicate,
        action="provider.merged_into",
        metadata={"survivor_provider_id": str(survivor.pk)},
    )
    return survivor
