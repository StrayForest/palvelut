import struct
import zlib

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from palvelut.apps.providers.models import (
    ContactChannel,
    MediaAsset,
    Provider,
    ProviderLanguage,
    ProviderMembership,
    ProviderService,
    ServiceArea,
)
from palvelut.apps.providers.workspace_forms import ProviderProfileForm
from palvelut.apps.providers.workspace_services import (
    autosave_revision,
    stage_media_upload,
    submit_revision,
)
from palvelut.apps.publishing.workflow import approve_revision
from palvelut.apps.taxonomy.models import (
    Category,
    Country,
    Language,
    Municipality,
    Region,
)


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(kind)
    crc = zlib.crc32(data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def _one_pixel_png() -> bytes:
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    raw = b"\x00\xff\x00\x00\xff"
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(raw))
        + _png_chunk(b"IEND", b"")
    )


class ProviderStructuredWorkspaceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="structured-owner@example.test",
            password="test-only-pass",
        )
        self.staff = user_model.objects.create_user(
            username="structured-staff@example.test",
            password="test-only-pass",
            is_staff=True,
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.DRAFT,
            claim_status=Provider.ClaimStatus.APPROVED,
            legal_name="Structured Oy",
            display_name="Structured",
            y_tunnus="2345678-9",
        )
        ProviderMembership.objects.create(
            provider=self.provider,
            account=self.owner,
            role=ProviderMembership.Role.OWNER,
        )
        self.category = Category.objects.create(slug="massage", name="Massage")
        country = Country.objects.create(code="FI", name="Finland")
        region = Region.objects.create(country=country, code="UUS", name="Uusimaa")
        self.municipality = Municipality.objects.create(
            region=region,
            code="091",
            name="Helsinki",
        )
        self.language = Language.objects.create(code="ru", name="Russian")

    def payload(self):
        return {
            "provider_type": "business",
            "legal_name": "Structured Oy",
            "display_name": "Structured Pro",
            "y_tunnus": "2345678-9",
            "contacts": [
                {
                    "kind": "phone",
                    "value": "+358401234567",
                    "label": "Call",
                    "is_public": True,
                    "sort_order": 0,
                }
            ],
            "services": [
                {
                    "category_id": str(self.category.pk),
                    "title": "Sports massage",
                    "description": "60 minute appointment",
                    "price_text": "60 €",
                    "is_active": True,
                }
            ],
            "service_areas": [
                {
                    "municipality_id": str(self.municipality.pk),
                    "mode": "onsite",
                }
            ],
            "languages": [{"language_id": str(self.language.pk), "declared": True}],
        }

    def test_form_validates_and_normalizes_structured_profile_data(self):
        data = self.payload()
        data.update(
            {
                "contacts": '[{"kind":"phone","value":"+358401234567"}]',
                "services": (
                    '[{"category_id":"%s","title":"Sports massage",'
                    '"price_text":"60 €"}]' % self.category.pk
                ),
                "service_areas": (
                    '[{"municipality_id":"%s","mode":"onsite"}]' % self.municipality.pk
                ),
                "languages": (
                    '[{"language_id":"%s","declared":true}]' % self.language.pk
                ),
            }
        )
        form = ProviderProfileForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        cleaned = form.cleaned_payload()
        self.assertEqual(cleaned["services"][0]["price_text"], "60 €")
        self.assertEqual(cleaned["service_areas"][0]["mode"], "onsite")

    def test_approval_atomically_promotes_structured_draft_to_live_state(self):
        autosave_revision(
            provider_id=self.provider.pk,
            account=self.owner,
            payload=self.payload(),
        )
        revision = submit_revision(provider_id=self.provider.pk, account=self.owner)

        self.assertFalse(ContactChannel.objects.filter(provider=self.provider).exists())
        self.assertFalse(
            ProviderService.objects.filter(provider=self.provider).exists()
        )

        approve_revision(revision_id=revision.pk, actor=self.staff)

        contact = ContactChannel.objects.get(provider=self.provider)
        service = ProviderService.objects.get(provider=self.provider)
        area = ServiceArea.objects.get(provider=self.provider)
        language = ProviderLanguage.objects.get(provider=self.provider)
        self.assertEqual(contact.value, "+358401234567")
        self.assertEqual(service.price_text, "60 €")
        self.assertEqual(service.category_id, self.category.pk)
        self.assertEqual(area.municipality_id, self.municipality.pk)
        self.assertEqual(language.language_id, self.language.pk)

    @override_settings(
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
            },
        }
    )
    def test_uploaded_image_is_staged_in_revision_until_approval(self):
        upload = SimpleUploadedFile(
            "photo.png",
            _one_pixel_png(),
            content_type="image/png",
        )
        revision = stage_media_upload(
            provider_id=self.provider.pk,
            account=self.owner,
            uploaded_file=upload,
            alt_text="Treatment room",
        )
        self.assertEqual(len(revision.payload["media"]), 1)
        self.assertTrue(
            revision.payload["media"][0]["storage_key"].startswith(
                f"provider-media/staging/{self.provider.pk}/"
            )
        )
        self.assertEqual(revision.payload["media"][0]["width"], 1)
        self.assertEqual(revision.payload["media"][0]["height"], 1)
        self.assertFalse(MediaAsset.objects.filter(provider=self.provider).exists())

        submitted = submit_revision(provider_id=self.provider.pk, account=self.owner)
        approve_revision(revision_id=submitted.pk, actor=self.staff)
        media = MediaAsset.objects.get(provider=self.provider)
        self.assertEqual(media.alt_text, "Treatment room")
        self.assertEqual(media.content_type, "image/png")
