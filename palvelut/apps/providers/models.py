from django.conf import settings
from django.db import models

from palvelut.apps.taxonomy.models import (
    Category,
    Language,
    Municipality,
    UuidV7Model,
)


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

    class ClaimStatus(models.TextChoices):
        UNCLAIMED = "unclaimed", "Unclaimed"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    provider_type = models.CharField(max_length=16, choices=Type.choices)
    lifecycle = models.CharField(
        max_length=24,
        choices=Lifecycle.choices,
        default=Lifecycle.UNCLAIMED,
    )
    claim_status = models.CharField(
        max_length=16,
        choices=ClaimStatus.choices,
        default=ClaimStatus.UNCLAIMED,
    )
    claim_evidence = models.JSONField(default=dict)
    legal_name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200)
    y_tunnus = models.CharField(max_length=16, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_name", "id")
        constraints = (
            models.CheckConstraint(
                condition=models.Q(provider_type__in=("individual", "business")),
                name="providers_provider_type_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    lifecycle__in=(
                        "unclaimed",
                        "draft",
                        "pending",
                        "published",
                        "changes_requested",
                        "suspended",
                        "archived",
                    )
                ),
                name="providers_provider_lifecycle_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    claim_status__in=(
                        "unclaimed",
                        "pending",
                        "approved",
                        "rejected",
                    )
                ),
                name="providers_provider_claim_status_valid",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(lifecycle="published")
                    | models.Q(claim_status="approved")
                ),
                name="providers_provider_published_requires_approved_claim",
            ),
            models.UniqueConstraint(
                fields=("y_tunnus",),
                condition=~models.Q(y_tunnus=""),
                name="providers_provider_y_tunnus_unique_nonblank",
            ),
        )

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

    class Meta:
        constraints = (
            models.CheckConstraint(
                condition=models.Q(role__in=("owner", "editor")),
                name="providers_membership_role_valid",
            ),
            models.UniqueConstraint(
                fields=("provider", "account"),
                name="providers_membership_provider_account_unique",
            ),
            models.UniqueConstraint(
                fields=("provider",),
                condition=models.Q(role="owner", is_active=True),
                name="providers_membership_one_active_owner",
            ),
        )


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

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("provider", "category", "title"),
                name="providers_service_provider_category_title_unique",
            ),
        )


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

    class Meta:
        constraints = (
            models.CheckConstraint(
                condition=models.Q(mode__in=("onsite", "travel", "remote")),
                name="providers_service_area_mode_valid",
            ),
            models.UniqueConstraint(
                fields=("provider", "municipality", "mode"),
                name="providers_service_area_provider_municipality_mode_unique",
            ),
        )


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

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("provider", "language"),
                name="providers_language_provider_language_unique",
            ),
        )


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

    class Meta:
        constraints = (
            models.CheckConstraint(
                condition=models.Q(
                    kind__in=(
                        "phone",
                        "email",
                        "website",
                        "booking",
                        "telegram",
                        "whatsapp",
                    )
                ),
                name="providers_contact_kind_valid",
            ),
            models.UniqueConstraint(
                fields=("provider", "kind", "value"),
                name="providers_contact_provider_kind_value_unique",
            ),
        )


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

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=("provider", "storage_key"),
                name="providers_media_provider_storage_key_unique",
            ),
        )
