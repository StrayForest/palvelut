from collections.abc import Mapping
from typing import Any

from django.contrib.auth.models import AbstractBaseUser

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import Provider


def record_audit(
    *,
    actor: AbstractBaseUser,
    action: str,
    provider: Provider | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> AuditEvent:
    return AuditEvent.objects.create(
        actor=actor,
        action=action,
        provider=provider,
        metadata=dict(metadata or {}),
    )
