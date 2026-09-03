from dataclasses import dataclass

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from palvelut.apps.providers.models import (
    ContactChannel,
    Provider,
    ProviderLanguage,
    ProviderService,
    ServiceArea,
)
from palvelut.apps.taxonomy.models import Category, Language, Municipality


@dataclass(frozen=True)
class DemoProvider:
    legal_name: str
    display_name: str
    provider_type: str
    lifecycle: str
    municipality_code: str
    category_slug: str
    email: str
    y_tunnus: str = ""


DEMO_PROVIDERS = (
    DemoProvider(
        legal_name="Synthetic Helsinki Accounting Oy",
        display_name="Synthetic Helsinki Accounting",
        provider_type="business",
        lifecycle="published",
        municipality_code="091",
        category_slug="accounting",
        email="helsinki-accounting@example.invalid",
        y_tunnus="0000000-0",
    ),
    DemoProvider(
        legal_name="Synthetic Espoo Legal Specialist",
        display_name="Synthetic Espoo Legal Specialist",
        provider_type="individual",
        lifecycle="draft",
        municipality_code="049",
        category_slug="legal",
        email="espoo-legal@example.invalid",
    ),
    DemoProvider(
        legal_name="Synthetic Vantaa Car Repair Oy",
        display_name="Synthetic Vantaa Car Repair",
        provider_type="business",
        lifecycle="unclaimed",
        municipality_code="092",
        category_slug="car-repair",
        email="vantaa-repair@example.invalid",
        y_tunnus="0000001-9",
    ),
    DemoProvider(
        legal_name="Synthetic Helsinki Massage Specialist",
        display_name="Synthetic Helsinki Massage Specialist",
        provider_type="individual",
        lifecycle="suspended",
        municipality_code="091",
        category_slug="massage-physiotherapy",
        email="helsinki-massage@example.invalid",
    ),
)


class Command(BaseCommand):
    help = "Create deterministic, clearly synthetic local demo providers."

    def handle(self, *args: object, **options: object) -> None:
        if settings.ENVIRONMENT not in {"local", "test"}:
            raise CommandError(
                "seed_demo is restricted to local/test environments; "
                f"refusing PALVELUT_ENVIRONMENT={settings.ENVIRONMENT!r}"
            )

        with transaction.atomic():
            russian, _ = Language.objects.update_or_create(
                code="ru",
                defaults={"name": "Russian"},
            )
            for spec in DEMO_PROVIDERS:
                municipality = self._municipality(spec.municipality_code)
                category = self._category(spec.category_slug)
                is_published = spec.lifecycle == Provider.Lifecycle.PUBLISHED
                provider, _ = Provider.objects.update_or_create(
                    legal_name=spec.legal_name,
                    defaults={
                        "display_name": spec.display_name,
                        "provider_type": spec.provider_type,
                        "lifecycle": spec.lifecycle,
                        "claim_status": (
                            Provider.ClaimStatus.APPROVED
                            if is_published
                            else Provider.ClaimStatus.UNCLAIMED
                        ),
                        "claim_evidence": (
                            {"source": "synthetic_demo"} if is_published else {}
                        ),
                        "y_tunnus": spec.y_tunnus,
                    },
                )
                ProviderService.objects.update_or_create(
                    provider=provider,
                    category=category,
                    title="Synthetic demo service",
                    defaults={
                        "description": "Synthetic local demo data. Not a real provider.",
                        "price_text": "Synthetic",
                        "is_active": True,
                    },
                )
                ServiceArea.objects.get_or_create(
                    provider=provider,
                    municipality=municipality,
                    mode=ServiceArea.Mode.ONSITE,
                )
                ProviderLanguage.objects.update_or_create(
                    provider=provider,
                    language=russian,
                    defaults={"declared": True},
                )
                ContactChannel.objects.update_or_create(
                    provider=provider,
                    kind=ContactChannel.Kind.EMAIL,
                    value=spec.email,
                    defaults={
                        "label": "Synthetic demo contact",
                        "is_public": True,
                        "sort_order": 0,
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(DEMO_PROVIDERS)} deterministic synthetic demo providers."
            )
        )

    @staticmethod
    def _municipality(code: str) -> Municipality:
        try:
            return Municipality.objects.get(region__country__code="FI", code=code)
        except Municipality.DoesNotExist as exc:
            raise CommandError(
                "Finland taxonomy seed is missing; run migrations before seed_demo."
            ) from exc

    @staticmethod
    def _category(slug: str) -> Category:
        try:
            return Category.objects.get(slug=slug)
        except Category.DoesNotExist as exc:
            raise CommandError(
                "Launch category seed is missing; run migrations before seed_demo."
            ) from exc
