from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone
from django.utils.translation import gettext

from palvelut.apps.providers.models import Provider

from .models import VerificationCheck
from .registry import get_registry_check_type


TRUST_EXPLANATION = gettext(
    "Verification labels show only the fact checked, official source and check date. "
    "They do not rate service quality or imply an unchecked licence."
)


@dataclass(frozen=True)
class PublicVerificationFact:
    kind: str
    fact: str
    source: str
    checked_at: datetime
    checked_date: str
    source_url: str

    @property
    def label(self) -> str:
        return f"{self.fact} in {self.source} · checked {self.checked_date}"


def _public_fact_name(kind: str) -> str:
    if kind == "business_identity":
        return "Y-tunnus found"
    if kind == "professional_right":
        return "Professional right found"
    return kind.replace("_", " ").capitalize()


def public_verification_facts(
    provider: Provider,
    *,
    at: datetime | None = None,
    limit: int | None = None,
) -> list[PublicVerificationFact]:
    """Return latest currently valid verified facts, one per check kind."""

    now = at or timezone.now()
    checks = (
        provider.verification_checks.filter(status=VerificationCheck.Status.VERIFIED)
        .filter(expires_at__isnull=True)
        .union(
            provider.verification_checks.filter(
                status=VerificationCheck.Status.VERIFIED,
                expires_at__gt=now,
            )
        )
        .order_by("kind", "-checked_at", "-id")
    )

    facts: list[PublicVerificationFact] = []
    seen_kinds: set[str] = set()
    for check in checks:
        if check.kind in seen_kinds:
            continue
        definition = get_registry_check_type(check.kind, require_enabled=False)
        facts.append(
            PublicVerificationFact(
                kind=check.kind,
                fact=_public_fact_name(check.kind),
                source=definition.source_name,
                checked_at=check.checked_at,
                checked_date=timezone.localtime(check.checked_at).date().isoformat(),
                source_url=check.source_url,
            )
        )
        seen_kinds.add(check.kind)
        if limit is not None and len(facts) >= limit:
            break
    return facts
