from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from palvelut.apps.moderation.models import AuditEvent

from .models import Provider, ProviderMembership
from .team_models import ProviderInvitation


def _lock_owner(provider: Provider, actor) -> ProviderMembership:
    membership = (
        ProviderMembership.objects.select_for_update()
        .filter(
            provider=provider,
            account=actor,
            role=ProviderMembership.Role.OWNER,
            is_active=True,
        )
        .first()
    )
    if membership is None:
        raise PermissionDenied("Only the active owner can manage provider membership.")
    return membership


@transaction.atomic
def invite_editor(*, provider: Provider, actor, invited_account) -> ProviderInvitation:
    provider = Provider.objects.select_for_update().get(pk=provider.pk)
    _lock_owner(provider, actor)
    if provider.provider_type != Provider.Type.BUSINESS:
        raise ValidationError(
            "Team invitations are available only for business providers."
        )
    if invited_account.pk == actor.pk:
        raise ValidationError("The owner cannot invite themselves.")
    if ProviderMembership.objects.filter(
        provider=provider,
        account=invited_account,
        is_active=True,
    ).exists():
        raise ValidationError("The account is already an active member.")

    invitation, created = ProviderInvitation.objects.get_or_create(
        provider=provider,
        invited_account=invited_account,
        status=ProviderInvitation.Status.PENDING,
        defaults={
            "invited_by": actor,
            "role": ProviderMembership.Role.EDITOR,
        },
    )
    if not created:
        raise ValidationError("A pending invitation already exists for this account.")

    AuditEvent.objects.create(
        provider=provider,
        actor=actor,
        action="provider.membership.invited",
        metadata={
            "invitation_id": str(invitation.pk),
            "account_id": str(invited_account.pk),
            "role": ProviderMembership.Role.EDITOR,
        },
    )
    return invitation


@transaction.atomic
def accept_invitation(*, invitation: ProviderInvitation, actor) -> ProviderMembership:
    invitation = (
        ProviderInvitation.objects.select_for_update()
        .select_related("provider")
        .get(pk=invitation.pk)
    )
    if invitation.invited_account_id != actor.pk:
        raise PermissionDenied("This invitation belongs to another account.")
    if invitation.status != ProviderInvitation.Status.PENDING:
        raise ValidationError("Invitation is no longer pending.")

    membership, _ = ProviderMembership.objects.update_or_create(
        provider=invitation.provider,
        account=actor,
        defaults={"role": ProviderMembership.Role.EDITOR, "is_active": True},
    )
    invitation.status = ProviderInvitation.Status.ACCEPTED
    invitation.accepted_at = timezone.now()
    invitation.save(update_fields=("status", "accepted_at"))
    AuditEvent.objects.create(
        provider=invitation.provider,
        actor=actor,
        action="provider.membership.accepted",
        metadata={
            "invitation_id": str(invitation.pk),
            "account_id": str(actor.pk),
            "role": ProviderMembership.Role.EDITOR,
        },
    )
    return membership


@transaction.atomic
def transfer_ownership(*, provider: Provider, actor, target_account) -> None:
    provider = Provider.objects.select_for_update().get(pk=provider.pk)
    current_owner = _lock_owner(provider, actor)
    if provider.provider_type != Provider.Type.BUSINESS:
        raise ValidationError(
            "Ownership transfer is available only for business providers."
        )
    if target_account.pk == actor.pk:
        raise ValidationError("The target account already owns this provider.")

    target = (
        ProviderMembership.objects.select_for_update()
        .filter(provider=provider, account=target_account, is_active=True)
        .first()
    )
    if target is None:
        raise ValidationError("Ownership can be transferred only to an active team member.")

    current_owner.role = ProviderMembership.Role.EDITOR
    current_owner.save(update_fields=("role",))
    target.role = ProviderMembership.Role.OWNER
    target.save(update_fields=("role",))

    AuditEvent.objects.create(
        provider=provider,
        actor=actor,
        action="provider.ownership.transferred",
        metadata={
            "from_account_id": str(actor.pk),
            "to_account_id": str(target_account.pk),
        },
    )
