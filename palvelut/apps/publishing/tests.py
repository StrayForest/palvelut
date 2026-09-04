from django.db import IntegrityError, transaction
from django.test import TestCase

from palvelut.apps.providers.models import ContactChannel, Provider

from .models import ProviderSlug


class DuplicateIdentityDeterminismTests(TestCase):
    def setUp(self) -> None:
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Canonical Oy",
            display_name="Canonical",
            y_tunnus="1234567-8",
        )
        self.other_provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Other Oy",
            display_name="Other",
            y_tunnus="7654321-0",
        )

    def assert_integrity_error(self, callback) -> None:  # type: ignore[no-untyped-def]
        with self.assertRaises(IntegrityError), transaction.atomic():
            callback()

    def test_duplicate_y_tunnus_is_rejected(self) -> None:
        self.assert_integrity_error(
            lambda: Provider.objects.create(
                provider_type=Provider.Type.BUSINESS,
                legal_name="Duplicate Oy",
                display_name="Duplicate",
                y_tunnus=self.provider.y_tunnus,
            )
        )

    def test_duplicate_contact_on_same_provider_is_rejected(self) -> None:
        ContactChannel.objects.create(
            provider=self.provider,
            kind=ContactChannel.Kind.EMAIL,
            value="owner@example.invalid",
        )
        self.assert_integrity_error(
            lambda: ContactChannel.objects.create(
                provider=self.provider,
                kind=ContactChannel.Kind.EMAIL,
                value="owner@example.invalid",
            )
        )

    def test_slug_is_globally_unique_and_current_slug_is_singular(self) -> None:
        ProviderSlug.objects.create(provider=self.provider, slug="canonical")
        self.assert_integrity_error(
            lambda: ProviderSlug.objects.create(
                provider=self.other_provider,
                slug="canonical",
            )
        )
        self.assert_integrity_error(
            lambda: ProviderSlug.objects.create(
                provider=self.provider,
                slug="canonical-new",
            )
        )

    def test_previous_slug_can_be_retained_for_redirect_history(self) -> None:
        previous = ProviderSlug.objects.create(
            provider=self.provider,
            slug="canonical-old",
            is_current=False,
        )
        current = ProviderSlug.objects.create(
            provider=self.provider,
            slug="canonical",
        )

        self.assertFalse(previous.is_current)
        self.assertTrue(current.is_current)
        self.assertEqual(self.provider.slugs.count(), 2)
