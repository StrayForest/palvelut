from django.conf import settings
from django.db import models

from palvelut.apps.providers.models import Provider
from palvelut.apps.taxonomy.models import UuidV7Model


class VerificationCheck(UuidV7Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="verification_checks",
    )
    kind = models.CharField(max_length=80)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    source_url = models.URLField(max_length=500, blank=True)
    evidence_metadata = models.JSONField(default=dict)
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="verification_checks",
    )
    checked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-checked_at", "-id")


class ProviderClaim(UuidV7Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    class EvidenceType(models.TextChoices):
        REGISTRY_SIGNATORY = "registry_signatory", "Registry signatory"
        BUSINESS_DOMAIN_EMAIL = "business_domain_email", "Business-domain email"
        STAFF_EQUIVALENT = "staff_equivalent", "Staff-reviewed equivalent"

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="claims",
    )
    claimant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="provider_claims",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    evidence_type = models.CharField(max_length=32, choices=EvidenceType.choices)
    evidence_metadata = models.JSONField(default=dict)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_provider_claims",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-requested_at", "-id")
        constraints = (
            models.CheckConstraint(
                condition=models.Q(status__in=("pending", "approved", "rejected")),
                name="verification_claim_status_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    evidence_type__in=(
                        "registry_signatory",
                        "business_domain_email",
                        "staff_equivalent",
                    )
                ),
                name="verification_claim_evidence_type_valid",
            ),
            models.UniqueConstraint(
                fields=("provider",),
                condition=models.Q(status="pending"),
                name="verification_claim_one_pending_per_provider",
            ),
        )
