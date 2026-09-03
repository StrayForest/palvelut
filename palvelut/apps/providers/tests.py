from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from palvelut.apps.moderation.models import AuditEvent, ModerationCase, ModerationEvent
from palvelut.apps.publishing.models import ProfileRevision
from palvelut.apps.taxonomy.models import (
    Category,
    Country,
    Language,
    Municipality,
    Region,
)
from palvelut.apps.verification.models import VerificationCheck

from .models import (
    ContactChannel,
    MediaAsset,
    Provider,
    ProviderLanguage,
    ProviderMembership,
    ProviderService,
    ServiceArea,
)


class DomainModelFoundationTests(TestCase):
    def test_provider_graph_persists_with_actor_timestamps(self) -> None:
        user = get_user_model().objects.create_user(username="staff")
        country = Country.objects.create(code="FI", name="Finland")
        region = Region.objects.create(country=country, code="UUS", name="Uusimaa")
        municipality = Municipality.objects.create(
            region=region,
            code="091",
            name="Helsinki",
        )
        category = Category.objects.create(slug="massage", name="Massage")
        language = Language.objects.create(code="ru", name="Russian")
        provider = Provider.objects.create(
            provider_type=Provider.Type.INDIVIDUAL,
            legal_name="Synthetic Provider",
            display_name="Synthetic Provider",
        )

        ProviderMembership.objects.create(provider=provider, account=user, role="owner")
        ProviderService.objects.create(provider=provider, category=category)
        ServiceArea.objects.create(provider=provider, municipality=municipality)
        ProviderLanguage.objects.create(provider=provider, language=language)
        ContactChannel.objects.create(
            provider=provider,
            kind="email",
            value="example.invalid",
        )
        MediaAsset.objects.create(
            provider=provider,
            storage_key="synthetic/example.webp",
            content_type="image/webp",
        )
        revision = ProfileRevision.objects.create(
            provider=provider,
            created_by=user,
            payload={"name": "Synthetic"},
        )
        verification = VerificationCheck.objects.create(
            provider=provider,
            kind="identity",
            checked_by=user,
        )
        case = ModerationCase.objects.create(
            provider=provider,
            reason="review",
            opened_by=user,
        )
        event = ModerationEvent.objects.create(
            case=case,
            event_type="opened",
            actor=user,
        )
        audit = AuditEvent.objects.create(
            provider=provider,
            actor=user,
            action="provider.created",
        )

        self.assertEqual(provider.services.count(), 1)
        self.assertEqual(provider.service_areas.count(), 1)
        self.assertEqual(provider.languages.count(), 1)
        self.assertIsNotNone(revision.created_at)
        self.assertIsNotNone(verification.checked_at)
        self.assertIsNotNone(event.created_at)
        self.assertIsNotNone(audit.created_at)


class ProviderDatabaseConstraintTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(username="owner")
        self.second_user = get_user_model().objects.create_user(username="owner-2")
        self.country = Country.objects.create(code="FI", name="Finland")
        self.region = Region.objects.create(
            country=self.country,
            code="UUS",
            name="Uusimaa",
        )
        self.municipality = Municipality.objects.create(
            region=self.region,
            code="091",
            name="Helsinki",
        )
        self.category = Category.objects.create(slug="massage", name="Massage")
        self.language = Language.objects.create(code="ru", name="Russian")
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            legal_name="Synthetic Oy",
            display_name="Synthetic",
            y_tunnus="1234567-8",
        )

    def assert_integrity_error(self, callback) -> None:  # type: ignore[no-untyped-def]
        with self.assertRaises(IntegrityError), transaction.atomic():
            callback()

    def test_provider_lifecycle_is_database_constrained(self) -> None:
        self.assert_integrity_error(
            lambda: Provider.objects.filter(pk=self.provider.pk).update(
                lifecycle="not-a-lifecycle"
            )
        )

    def test_nonblank_y_tunnus_is_unique(self) -> None:
        self.assert_integrity_error(
            lambda: Provider.objects.create(
                provider_type=Provider.Type.BUSINESS,
                legal_name="Duplicate Oy",
                display_name="Duplicate",
                y_tunnus=self.provider.y_tunnus,
            )
        )

    def test_provider_has_at_most_one_active_owner(self) -> None:
        ProviderMembership.objects.create(
            provider=self.provider,
            account=self.user,
            role=ProviderMembership.Role.OWNER,
        )
        self.assert_integrity_error(
            lambda: ProviderMembership.objects.create(
                provider=self.provider,
                account=self.second_user,
                role=ProviderMembership.Role.OWNER,
            )
        )

    def test_membership_is_unique_per_provider_and_account(self) -> None:
        ProviderMembership.objects.create(
            provider=self.provider,
            account=self.user,
            role=ProviderMembership.Role.EDITOR,
        )
        self.assert_integrity_error(
            lambda: ProviderMembership.objects.create(
                provider=self.provider,
                account=self.user,
                role=ProviderMembership.Role.EDITOR,
                is_active=False,
            )
        )

    def test_provider_relations_reject_duplicate_rows(self) -> None:
        ProviderService.objects.create(
            provider=self.provider,
            category=self.category,
            title="",
        )
        self.assert_integrity_error(
            lambda: ProviderService.objects.create(
                provider=self.provider,
                category=self.category,
                title="",
            )
        )

        ServiceArea.objects.create(
            provider=self.provider,
            municipality=self.municipality,
            mode=ServiceArea.Mode.ONSITE,
        )
        self.assert_integrity_error(
            lambda: ServiceArea.objects.create(
                provider=self.provider,
                municipality=self.municipality,
                mode=ServiceArea.Mode.ONSITE,
            )
        )

        ProviderLanguage.objects.create(
            provider=self.provider,
            language=self.language,
        )
        self.assert_integrity_error(
            lambda: ProviderLanguage.objects.create(
                provider=self.provider,
                language=self.language,
            )
        )

    def test_contacts_and_media_reject_exact_duplicates(self) -> None:
        ContactChannel.objects.create(
            provider=self.provider,
            kind=ContactChannel.Kind.EMAIL,
            value="synthetic@example.invalid",
        )
        self.assert_integrity_error(
            lambda: ContactChannel.objects.create(
                provider=self.provider,
                kind=ContactChannel.Kind.EMAIL,
                value="synthetic@example.invalid",
            )
        )

        MediaAsset.objects.create(
            provider=self.provider,
            storage_key="synthetic/example.webp",
            content_type="image/webp",
        )
        self.assert_integrity_error(
            lambda: MediaAsset.objects.create(
                provider=self.provider,
                storage_key="synthetic/example.webp",
                content_type="image/webp",
            )
        )
