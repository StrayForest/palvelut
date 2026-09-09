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
CURRENT_PROVIDER_TERMS_VERSION = "2026-09-10"


def _require_authenticated(actor: AbstractBaseUser) -> None:
    if not actor.is_authenticated:
        raise PermissionDenied("Provider account is required")


def _require_staff(actor: AbstractBaseUser) -> None:
    if not actor.is_authenticated or not actor.is_staff:
        raise PermissionDenied("Staff access is required")


def _validate_provider_eligibility(
    *,
    provider: Provider,
    professional_right_reference: str,
    employer_authorization_reference: str,
) -> tuple[str, str]:
    professional_right_reference = professional_right_reference.strip()
    employer_authorization_reference = employer_authorization_reference.strip()

    if provider.provider_type == Provider.Type.BUSINESS:
        if not provider.y_tunnus.strip():
            raise ValidationError("Y-tunnus is required for a commercial provider")
        return "", ""

    if provider.provider_type == Provider.Type.INDIVIDUAL:
        if not professional_right_reference:
            raise ValidationError(
                "Official professional-right evidence is required for an employed regulated professional"
            )
        if not employer_authorization_reference:
            raise ValidationError(
                "Employer authorization is required for an employed regulated professional"
            )
        return professional_right_reference, employer_authorization_reference

    raise ValidationError("Unsupported provider type")


@transaction.atomic
def submit_provider_claim(
    *,
    provider_id: object,
    actor: AbstractBaseUser,
    evidence_kind: ClaimEvidenceKind,
    evidence_reference: str,
    provider_terms_accepted: bool,
    professional_right_reference: str = "",
    employer_authorization_reference: str = "",
) -> Provider:
    _require_authenticated(actor)
    if actor.is_staff:
        raise ValidationError("Staff accounts cannot claim provider ownership")
    if not provider_terms_accepted:
        raise ValidationError("Current provider terms must be accepted")
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

    professional_right_reference, employer_authorization_reference = (
        _validate_provider_eligibility(
            provider=provider,
            professional_right_reference=professional_right_reference,
            employer_authorization_reference=employer_authorization_reference,
        )
    )
    submitted_at = timezone.now()
    provider.claim_status = Provider.ClaimStatus.PENDING
    provider.claim_evidence = {
        "kind": evidence_kind,
        "reference": reference,
        "claimant_user_id": str(actor.pk),
        "submitted_at": submitted_at.isoformat(),
        "provider_terms_version": CURRENT_PROVIDER_TERMS_VERSION,
        "provider_terms_accepted_at": submitted_at.isoformat(),
        "professional_right_reference": professional_right_reference,
        "employer_authorization_reference": employer_authorization_reference,
    }
    provider.save(update_fields=("claim_status", "claim_evidence", "updated_at"))
    AuditEvent.objects.create(
        provider=provider,
        actor=actor,
        action="provider.claim_submitted",
        metadata={
            "evidence_kind": evidence_kind,
            "provider_terms_version": CURRENT_PROVIDER_TERMS_VERSION,
        },
    )
    return provider


@transaction.atomic
def start_new_provider_claim(
    *,
    actor: AbstractBaseUser,
    provider_type: str,
    legal_name: str,
    display_name: str,
    y_tunnus: str,
    evidence_kind: ClaimEvidenceKind,
    evidence_reference: str,
    provider_terms_accepted: bool,
    professional_right_reference: str = "",
    employer_authorization_reference: str = "",
) -> Provider:
    _require_authenticated(actor)
    if actor.is_staff:
        raise ValidationError("Staff accounts cannot start provider ownership claims")
    if provider_type not in Provider.Type.values:
        raise ValidationError("Unsupported provider type")

    legal_name = legal_name.strip()
    display_name = display_name.strip()
    y_tunnus = y_tunnus.strip()
    if not legal_name or not display_name:
        raise ValidationError("Provider legal and display names are required")
    if provider_type == Provider.Type.BUSINESS and not y_tunnus:
        raise ValidationError("Y-tunnus is required for a commercial provider")
    if y_tunnus and Provider.objects.filter(y_tunnus=y_tunnus).exists():
        raise ValidationError(
            "A provider with this Y-tunnus already exists; claim the existing draft instead"
        )
    if Provider.objects.filter(
        claim_status=Provider.ClaimStatus.PENDING,
        claim_evidence__claimant_user_id=str(actor.pk),
    ).exists():
        raise ValidationError("An ownership claim is already pending for this account")

    provider = Provider.objects.create(
        provider_type=provider_type,
        lifecycle=Provider.Lifecycle.UNCLAIMED,
        claim_status=Provider.ClaimStatus.UNCLAIMED,
        legal_name=legal_name,
        display_name=display_name,
        y_tunnus=y_tunnus,
    )
    return submit_provider_claim(
        provider_id=provider.pk,
        actor=actor,
        evidence_kind=evidence_kind,
        evidence_reference=evidence_reference,
        provider_terms_accepted=provider_terms_accepted,
        professional_right_reference=professional_right_reference,
        employer_authorization_reference=employer_authorization_reference,
    )


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

    if evidence.get("kind") not in ALLOWED_CLAIM_EVIDENCE:
        raise ValidationError("Claim lacks independent business-control evidence")
    if evidence.get("provider_terms_version") != CURRENT_PROVIDER_TERMS_VERSION:
        raise ValidationError(
            "Claim does not include acceptance of the current provider terms"
        )
    if not evidence.get("provider_terms_accepted_at"):
        raise ValidationError("Provider terms acceptance timestamp is missing")
    _validate_provider_eligibility(
        provider=provider,
        professional_right_reference=str(
            evidence.get("professional_right_reference", "")
        ),
        employer_authorization_reference=str(
            evidence.get("employer_authorization_reference", "")
        ),
    )
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