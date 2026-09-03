from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from palvelut.apps.providers.management.commands.seed_demo import DEMO_PROVIDERS
from palvelut.apps.providers.models import Provider


class SeedDemoCommandTests(TestCase):
    def test_seed_demo_is_idempotent_and_covers_launch_shape(self) -> None:
        call_command("seed_demo", stdout=StringIO())
        first_ids = tuple(
            Provider.objects.get(legal_name=spec.legal_name).id for spec in DEMO_PROVIDERS
        )

        call_command("seed_demo", stdout=StringIO())
        second_ids = tuple(
            Provider.objects.get(legal_name=spec.legal_name).id for spec in DEMO_PROVIDERS
        )

        self.assertEqual(first_ids, second_ids)
        self.assertEqual(
            Provider.objects.filter(
                legal_name__in=[spec.legal_name for spec in DEMO_PROVIDERS]
            ).count(),
            len(DEMO_PROVIDERS),
        )

        providers = list(
            Provider.objects.filter(
                legal_name__in=[spec.legal_name for spec in DEMO_PROVIDERS]
            ).prefetch_related("service_areas__municipality", "services__category", "languages__language")
        )
        self.assertEqual(
            {provider.provider_type for provider in providers},
            {Provider.Type.INDIVIDUAL, Provider.Type.BUSINESS},
        )
        self.assertTrue(
            {
                Provider.Lifecycle.UNCLAIMED,
                Provider.Lifecycle.DRAFT,
                Provider.Lifecycle.PUBLISHED,
                Provider.Lifecycle.SUSPENDED,
            }.issubset({provider.lifecycle for provider in providers})
        )
        self.assertEqual(
            {
                area.municipality.name
                for provider in providers
                for area in provider.service_areas.all()
            },
            {"Helsinki", "Espoo", "Vantaa"},
        )
        for provider in providers:
            self.assertEqual(provider.services.count(), 1)
            self.assertEqual(provider.service_areas.count(), 1)
            self.assertEqual(
                {item.language.code for item in provider.languages.all()},
                {"ru"},
            )
            self.assertEqual(provider.contacts.count(), 1)
            self.assertIn("Synthetic", provider.display_name)

    @override_settings(ENVIRONMENT="production")
    def test_seed_demo_refuses_production(self) -> None:
        with self.assertRaisesMessage(CommandError, "restricted to local/test"):
            call_command("seed_demo", stdout=StringIO())

    @override_settings(ENVIRONMENT="staging")
    def test_seed_demo_refuses_staging(self) -> None:
        with self.assertRaisesMessage(CommandError, "restricted to local/test"):
            call_command("seed_demo", stdout=StringIO())
