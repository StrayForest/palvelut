from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable

from django.core.exceptions import ValidationError

from .adapters import PRH_YTJ_SOURCE, YtjPrhAdapter


@dataclass(frozen=True)
class RegistryCheckType:
    """Configuration contract for one official-source verification check."""

    kind: str
    source_name: str
    subject_field: str
    lookup_method: str
    regulated_category: bool
    enabled: bool
    legal_source_review: str | None = None
    adapter_factory: Callable[[], object] | None = None

    def validate_configuration(self) -> None:
        if self.regulated_category and self.enabled and not self.legal_source_review:
            raise RuntimeError(
                f"Regulated verification type {self.kind!r} cannot be enabled "
                "without a recorded legal/source review"
            )
        if self.enabled and self.adapter_factory is None:
            raise RuntimeError(
                f"Enabled verification type {self.kind!r} requires an adapter factory"
            )
        if self.enabled and (not self.subject_field or not self.lookup_method):
            raise RuntimeError(
                f"Enabled verification type {self.kind!r} requires subject and lookup fields"
            )


_registry = {
    "business_identity": RegistryCheckType(
        kind="business_identity",
        source_name=PRH_YTJ_SOURCE,
        subject_field="y_tunnus",
        lookup_method="lookup_business_id",
        regulated_category=False,
        enabled=True,
        adapter_factory=YtjPrhAdapter,
    ),
    # Deliberately disabled until a separate legal/source review establishes the
    # permitted source, wording, retention and re-check policy for regulated work.
    "professional_right": RegistryCheckType(
        kind="professional_right",
        source_name="JulkiTerhikki",
        subject_field="",
        lookup_method="",
        regulated_category=True,
        enabled=False,
        legal_source_review=None,
        adapter_factory=None,
    ),
}

for _definition in _registry.values():
    _definition.validate_configuration()

REGISTRY_CHECK_TYPES = MappingProxyType(_registry)


def get_registry_check_type(kind: str, *, require_enabled: bool = True) -> RegistryCheckType:
    try:
        definition = REGISTRY_CHECK_TYPES[kind]
    except KeyError as exc:
        raise ValidationError(f"Unsupported verification kind: {kind}") from exc

    definition.validate_configuration()
    if require_enabled and not definition.enabled:
        raise ValidationError(
            f"Verification kind {kind!r} is disabled pending legal/source review"
        )
    return definition
