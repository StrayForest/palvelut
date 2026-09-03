from django.conf import settings
from django.db import models

from palvelut.apps.taxonomy.models import Category, Language, Municipality, UuidV7Model


class Provider(UuidV7Model):
    class Type(models.TextChoices):
        INDIVIDUAL = "individual", "Individual"
        BUSINESS = "business", "Business"

    class Lifecycle(models.TextChoices):
        UNCLAIMED = "unclaimed", "Unclaimed"
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        PUBLISHED = "published", "Published"
        CHANGES_REQUESTED = "changes_requested", "Changes requested"
        SUSPENDED = "suspended", "Suspended"
        ARCHIVED = "archived", "Archived"

    provider_type = models.CharField(max_length=16, choices=Type.choices)
    lifecycle = models.CharField(
        max_length=24,
        choices=Lifecycle.choices,
        default=Lifecycle.UNCLAIMED,
    )
    legal_name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)
    y_tunnus = models.CharField(max_length=16, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_name", "id")

    def __str__(self) -> str:
        return self.display_name


class ProviderMembership(UuidV7Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        EDITOR = "editor", "Editor"

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="provider_memberships",
    )
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.EDITOR)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ProviderService(UuidV7Model):
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="services",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="provider_services",
    )
    title = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    price_text = models.CharField(max_length=160, blank=True)
    is_active = models.BooleanField(default=True)


class ServiceArea(UuidV7Model):
    class Mode(models.TextChoices):
        ONSITE = "onsite", "On-site"
        TRAVEL = "travel", "Travels to customer"
        REMOTE = "remote", "Remote"

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="service_areas",
    )
    municipality = models.ForeignKey(
        Municipality,
        on_delete=models.PROTECT,
        related_name="provider_service_areas",
    )
    mode = models.CharField(max_length=16, choices=Mode.choices, default=Mode.ONSITE)


class ProviderLanguage(UuidV7Model):
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="languages",
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name="providers",
    )
    declared = models.BooleanField(default=True)


class ContactChannel(UuidV7Model):
    class Kind(models.TextChoices):
        PHONE = "phone", "Phone"
        EMAIL = "email", "Email"
        WEBSITE = "website", "Website"
        BOOKING = "booking", "Booking"
        TELEGRAM = "telegram", "Telegram"
        WHATSAPP = "whatsapp", "WhatsApp"

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="contacts",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    value = models.CharField(max_length=500)
    label = models.CharField(max_length=80, blank=True)
    is_public = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)


class MediaAsset(UuidV7Model):
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="media_assets",
    )
    storage_key = models.CharField(max_length=500)
    content_type = models.CharField(max_length=120)
    alt_text = models.CharField(max_length=240, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
