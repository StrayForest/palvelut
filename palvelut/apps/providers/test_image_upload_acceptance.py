import struct
import zlib

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from palvelut.apps.providers.image_safety import sanitize_png
from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.providers.workspace_services import stage_media_upload
from palvelut.apps.publishing.models import ProfileRevision


def _chunk(kind: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(kind)
    crc = zlib.crc32(data, crc) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def _png(*, width: int = 1, height: int = 1, metadata: bool = False) -> bytes:
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + (b"\x11\x22\x33\xff" * width) for _ in range(height))
    parts = [b"\x89PNG\r\n\x1a\n", _chunk(b"IHDR", ihdr)]
    if metadata:
        parts.append(_chunk(b"tEXt", b"Comment\x00secret-metadata"))
    parts.extend((_chunk(b"IDAT", zlib.compress(raw)), _chunk(b"IEND", b"")))
    return b"".join(parts)


class ImageSafetyUnitTests(TestCase):
    def test_valid_png_is_reencoded_without_ancillary_metadata(self):
        original = _png(metadata=True)
        sanitized = sanitize_png(original)

        self.assertEqual((sanitized.width, sanitized.height), (1, 1))
        self.assertEqual(sanitized.content_type, "image/png")
        self.assertNotEqual(sanitized.data, original)
        self.assertNotIn(b"tEXt", sanitized.data)
        self.assertNotIn(b"secret-metadata", sanitized.data)
        self.assertEqual(sanitize_png(sanitized.data).data, sanitized.data)

    def test_spoofed_or_trailing_payload_is_rejected(self):
        with self.assertRaises(ValidationError):
            sanitize_png(b"GIF89a" + b"\x00" * 64)
        with self.assertRaises(ValidationError):
            sanitize_png(_png() + b"polyglot-tail")

    def test_pixel_bomb_is_rejected_before_inflation(self):
        ihdr = struct.pack(">IIBBBBB", 100_000, 100_000, 8, 6, 0, 0, 0)
        bomb = (
            b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(b"\x00"))
            + _chunk(b"IEND", b"")
        )
        with self.assertRaises(ValidationError):
            sanitize_png(bomb)


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class ImageUploadAcceptanceTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="image-owner@example.test",
            password="test-only-pass",
        )
        self.provider = Provider.objects.create(
            provider_type=Provider.Type.BUSINESS,
            lifecycle=Provider.Lifecycle.DRAFT,
            claim_status=Provider.ClaimStatus.APPROVED,
            legal_name="Image Safe Oy",
            display_name="Image Safe",
        )
        ProviderMembership.objects.create(
            provider=self.provider,
            account=self.owner,
            role=ProviderMembership.Role.OWNER,
        )

    def test_staged_bytes_are_sanitized_and_dimensions_are_recorded(self):
        upload = SimpleUploadedFile(
            "profile.png",
            _png(metadata=True),
            content_type="image/png",
        )
        revision = stage_media_upload(
            provider_id=self.provider.pk,
            account=self.owner,
            uploaded_file=upload,
            alt_text="Profile image",
        )
        media = revision.payload["media"][0]
        self.assertEqual((media["width"], media["height"]), (1, 1))
        with default_storage.open(media["storage_key"], "rb") as stored:
            stored_bytes = stored.read()
        self.assertNotIn(b"tEXt", stored_bytes)
        self.assertNotIn(b"secret-metadata", stored_bytes)
        self.assertEqual(sanitize_png(stored_bytes).data, stored_bytes)

    def test_spoofed_upload_creates_neither_revision_nor_staged_file(self):
        upload = SimpleUploadedFile(
            "profile.png",
            b"not a png",
            content_type="image/png",
        )
        with self.assertRaises(ValidationError):
            stage_media_upload(
                provider_id=self.provider.pk,
                account=self.owner,
                uploaded_file=upload,
            )
        self.assertFalse(
            ProfileRevision.objects.filter(provider=self.provider).exists()
        )
