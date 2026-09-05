from django import template

from palvelut.apps.providers.models import Provider
from palvelut.apps.verification.presentation import (
    TRUST_EXPLANATION,
    public_verification_facts,
)

register = template.Library()


@register.simple_tag
def verification_facts(provider: Provider, limit: int | None = None):
    return public_verification_facts(provider, limit=limit)


@register.simple_tag
def trust_explanation() -> str:
    return str(TRUST_EXPLANATION)
