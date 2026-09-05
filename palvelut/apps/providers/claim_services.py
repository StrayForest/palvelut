from __future__ import annotations

from typing import Literal

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import Provider, ProviderMembership

ClaimEvidenceKind = Literal[
    "registry_signatory",
    "business_domain_email",
    "staff_reviewed_equivalent",
]
ClaimDecision = Literal["approve", "reject"]

ALLOWED_CLAIM_EVIDENCE = {
    "registry_signatory",
    "business_domain_email",
    "staff_reviewed_equivalent",
}


def _require_authenticated(actor: AbstractBaseUser) -> None:
    if not actor.is_authenticated:
        raise PermissionDenied("Provider account is required")


def _require_staff(actor: AbstractBaseUser) -> None:
    if not actor.is_authenticated or not actor.is_staff:
        raise PermissionDenied("Staff access is required")


@transaction.atomic
def submit_provider_claim(
    *,
    provider_id: object,
    actor: AbstractBaseUser,
    evidence_kind: ClaimEvidenceKind,
    evidence_reference: str,
) -> Provider:
    _require_authenticated(actor)
    if actor.is_staff:
        raise ValidationError("Staff accounts cannot claim provider ownership")
    if evidence_kind not in ALLOWED_CLAIM_EVIDENCE:
        raise ValidationError("Independent business-control evidence is required")
    reference = evidence_reference.strip()
    if not reference:
        raise ValidationError("Evidence reference is required")

    provider = Provider.objects.select_for_update().get(pk=provider_id)
    if provider.lifecycle != Provider.Lifecycle.UNCLAIMED:
        raise ValidationError("Only an unclaimed draft can be claimed")
    if provider.claim_status not in {
        Provider.ClaimStatus.UNCLAIMED,
        Provider.ClaimStatus.REJECTED,
    }:
        raise ValidationError("A claim is already pending or approved")

    provider.claim_status = Provider.ClaimStatus.PENDING
    provider.claim_evidence = {
        "kind": evidence_kind,
        "reference": reference,
        "claimant_user_id": str(actor.pk),
        "submitted_at": timezone.now().isoformat(),
    }
    provider.save(update_fields=("claim_status", "claim_evidence", "updated_at"))
    AuditEvent.objects.create(
        provider=provider,
        actor=actor,
        action="provider.claim_submitted",
        metadata={"evidence_kind": evidence_kind},
    )
    return provider


@transaction.atomic
def resolve_provider_claim(
    *,
    provider_id: object,
    actor: AbstractBaseUser,
    decision: ClaimDecision,
    review_note: str = "",
) -> Provider:
    _require_staff(actor)
    if decision not in {"approve", "reject"}:
        raise ValidationError("Unsupported claim decision")

    provider = Provider.objects.select_for_update().get(pk=provider_id)
    if provider.claim_status != Provider.ClaimStatus.PENDING:
        raise ValidationError("Only a pending claim can be reviewed")
    evidence = dict(provider.claim_evidence or {})
    if evidence.get("kind") not in ALLOWED_CLAIM_EVIDENCE:
        raise ValidationError("Claim lacks independent business-control evidence")
    claimant_id = evidence.get("claimant_user_id")
    if not claimant_id:
        raise ValidationError("Claimant identity is missing")

    reviewed_at = timezone.now()
    evidence.update(
        {
            "decision": decision,
            "review_note": review_note.strip(),
            "reviewed_by_user_id": str(actor.pk),
            "reviewed_at": reviewed_at.isoformat(),
        }
    )
    provider.claim_evidence = evidence

    if decision == "reject":
        provider.claim_status = Provider.ClaimStatus.REJECTED
        provider.lifecycle = Provider.Lifecycle.UNCLAIMED
        provider.save(
            update_fields=("claim_status", "claim_evidence", "lifecycle", "updated_at")
        )
        AuditEvent.objects.create(
            provider=provider,
            actor=actor,
            action="provider.claim_rejected",
            metadata={"claimant_user_id": str(claimant_id)},
        )
        return provider

    if ProviderMembership.objects.filter(provider=provider, is_active=True).exists():
        raise ValidationError("Provider already has an active membership")
    provider.claim_status = Provider.ClaimStatus.APPROVED
    provider.lifecycle = Provider.Lifecycle.DRAFT
    provider.save(
        update_fields=("claim_status", "claim_evidence", "lifecycle", "updated_at")
    )
    ProviderMembership.objects.create(
        provider=provider,
        account_id=claimant_id,
        role=ProviderMembership.Role.OWNER,
        is_active=True,
    )
    AuditEvent.objects.create(
        provider=provider,
        actor=actor,
        action="provider.claim_approved",
        metadata={"claimant_user_id": str(claimant_id)},
    )
    return provider
