from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from palvelut.apps.moderation.services import moderate_provider
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision, ProviderSlug
from palvelut.apps.publishing.services import ensure_provider_slug


class ProviderSlugDeterminismTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_superuser(
            username="slug-staff",
            email="slug-staff@example.invalid",
            password="test-only-password",
        )

    def _provider(self, name: str) -> Provider:
        return Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name=f"{name} Oy",
            display_name=name,
            claim_status=Provider.ClaimStatus.APPROVED,
        )

    def test_same_display_name_gets_distinct_stable_slugs(self):
        first = self._provider("Sama Palvelu")
        second = self._provider("Sama Palvelu")

        first_slug = ensure_provider_slug(provider_id=first.pk)
        second_slug = ensure_provider_slug(provider_id=second.pk)

        self.assertNotEqual(first_slug.slug, second_slug.slug)
        self.assertTrue(first_slug.slug.endswith(str(first.pk)))
        self.assertTrue(second_slug.slug.endswith(str(second.pk)))
        self.assertEqual(
            ensure_provider_slug(provider_id=first.pk).pk,
            first_slug.pk,
        )
        self.assertEqual(ProviderSlug.objects.filter(provider=first).count(), 1)

    def test_slug_value_is_globally_unique(self):
        first = self._provider("First")
        second = self._provider("Second")
        slug = ensure_provider_slug(provider_id=first.pk)

        with self.assertRaises(IntegrityError), transaction.atomic():
            ProviderSlug.objects.create(
                provider=second,
                slug=slug.slug,
                is_current=True,
            )

    def test_publish_creates_slug_once(self):
        provider = self._provider("Published Provider")
        ProfileRevision.objects.create(
            provider=provider,
            status=ProfileRevision.Status.PENDING,
            payload={"display_name": "Published Provider"},
            created_by=self.staff,
        )

        moderate_provider(provider_id=provider.pk, actor=self.staff, action="approve")

        slug = ProviderSlug.objects.get(provider=provider, is_current=True)
        self.assertTrue(slug.slug.endswith(str(provider.pk)))
