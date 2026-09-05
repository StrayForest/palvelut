from django import template

from palvelut.apps.providers.models import Provider
from palvelut.apps.verification.presentation import public_verification_facts

register = template.Library()


@register.simple_tag
def verification_facts(provider: Provider, limit: int | None = None):
    return public_verification_facts(provider, limit=limit)
