from django.contrib.auth import get_user_model
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
