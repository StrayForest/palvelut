from __future__ import annotations

from django.db import transaction
from django.utils.text import slugify

from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProviderSlug

SLUG_MAX_LENGTH = 220


def _stable_slug(provider: Provider) -> str:
    suffix = str(provider.pk)
    max_base_length = SLUG_MAX_LENGTH - len(suffix) - 1
    base = slugify(provider.display_name, allow_unicode=True)[:max_base_length].strip("-")
    if not base:
        base = "provider"
    return f"{base}-{suffix}"


@transaction.atomic
def ensure_provider_slug(*, provider_id: object) -> ProviderSlug:
    provider = Provider.objects.select_for_update().get(pk=provider_id)
    current = ProviderSlug.objects.filter(provider=provider, is_current=True).first()
    if current is not None:
        return current

    slug, _ = ProviderSlug.objects.get_or_create(
        provider=provider,
        is_current=True,
        defaults={"slug": _stable_slug(provider)},
    )
    return slug
