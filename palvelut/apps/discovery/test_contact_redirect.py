from django.test import TestCase, override_settings

from palvelut.apps.analytics.models import AnalyticsEvent
from palvelut.apps.providers.models import ContactChannel, Provider


@override_settings(ALLOWED_HOSTS=["testserver"])
class ContactRedirectTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.PUBLISHED,
            claim_status=Provider.ClaimStatus.APPROVED,
            claim_evidence={"source": "test"},
            legal_name="Contact Test Oy",
            display_name="Contact Test",
            y_tunnus="7654321-0",
        )
        cls.phone = ContactChannel.objects.create(
            provider=cls.provider,
            kind=ContactChannel.Kind.PHONE,
            value="+358 40 123 4567",
            label="Call",
            is_public=True,
        )
        cls.private = ContactChannel.objects.create(
            provider=cls.provider,
            kind=ContactChannel.Kind.EMAIL,
            value="private@example.test",
            is_public=False,
        )

    def test_redirect_resolves_stored_target_and_records_minimal_event(self) -> None:
        response = self.client.get(
            f"/palvelut/en/go/{self.provider.id}/phone/",
            {"destination": "https://attacker.example/"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "tel:+358 40 123 4567")
        self.assertEqual(response["Cache-Control"], "private, no-store")
        event = AnalyticsEvent.objects.get()
        self.assertEqual(event.kind, AnalyticsEvent.Kind.CONTACT_CLICK)
        self.assertEqual(event.provider_id, self.provider.id)
        self.assertEqual(event.channel, ContactChannel.Kind.PHONE)
        self.assertFalse(hasattr(event, "destination"))

    def test_private_channel_is_not_resolved(self) -> None:
        response = self.client.get(f"/palvelut/en/go/{self.provider.id}/email/")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(AnalyticsEvent.objects.exists())

    def test_non_published_provider_is_not_resolved(self) -> None:
        self.provider.lifecycle = Provider.Lifecycle.SUSPENDED
        self.provider.save(update_fields=["lifecycle"])

        response = self.client.get(f"/palvelut/en/go/{self.provider.id}/phone/")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(AnalyticsEvent.objects.exists())

    def test_invalid_stored_destination_fails_closed_without_event(self) -> None:
        self.phone.value = "javascript:alert(1)"
        self.phone.save(update_fields=["value"])

        response = self.client.get(f"/palvelut/en/go/{self.provider.id}/phone/")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(AnalyticsEvent.objects.exists())
