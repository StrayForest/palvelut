from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone

from palvelut.apps.providers.models import Provider

from .models import VerificationCheck
from .registry import get_registry_check_type


TRUST_EXPLANATION = (
    "Метки проверки показывают только конкретный проверенный факт, официальный источник "
    "и дату проверки. Они не оценивают качество услуг и не подтверждают лицензии или "
    "профессиональные права, которые прямо не указаны в метке."
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
        return f"{self.fact} · источник: {self.source} · проверено {self.checked_date}"


def _public_fact_name(kind: str) -> str:
    if kind == "business_identity":
        return "Y-tunnus найден"
    if kind == "professional_right":
        return "Профессиональное право найдено"
    return "Проверенный факт"


def public_verification_facts(
    provider: Provider,
    *,
    at: datetime | None = None,
    limit: int | None = None,
) -> list[PublicVerificationFact]:
    """Return latest currently valid verified facts, one per check kind."""

    now = at or timezone.now()
    checks = sorted(
        (
            check
            for check in provider.verification_checks.all()
            if check.status == VerificationCheck.Status.VERIFIED
            and (check.expires_at is None or check.expires_at > now)
        ),
        key=lambda check: (check.kind, check.checked_at, check.id),
        reverse=True,
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
