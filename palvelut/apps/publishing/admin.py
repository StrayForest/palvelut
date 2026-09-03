from __future__ import annotations

import json

from django.contrib import admin
from django.db import transaction
from django.utils import timezone
from django.utils.html import format_html

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision


@admin.register(ProfileRevision)
class ProfileRevisionAdmin(admin.ModelAdmin):
    list_display = (
        "provider",
        "status",
        "created_by",
        "created_at",
        "reviewed_at",
    )
    list_filter = ("status",)
    search_fields = ("provider__display_name", "provider__legal_name")
    autocomplete_fields = ("provider", "created_by")
    readonly_fields = ("created_at", "reviewed_at", "payload_diff")
    actions = ("approve_revisions", "request_revision_changes")

    @admin.display(description="Diff against current provider")
    def payload_diff(self, obj: ProfileRevision) -> str:
        if not obj.pk:
            return "Save the revision to view a diff."
        current = {
            "legal_name": obj.provider.legal_name,
            "display_name": obj.provider.display_name,
            "y_tunnus": obj.provider.y_tunnus,
            "provider_type": obj.provider.provider_type,
        }
        changed = {
            key: {"current": current.get(key), "proposed": value}
            for key, value in obj.payload.items()
            if current.get(key) != value
        }
        if not changed:
            return "No provider-field changes."
        return format_html(
            "<pre>{}</pre>",
            json.dumps(changed, ensure_ascii=False, indent=2),
        )

    @admin.action(description="Approve selected revisions")
    def approve_revisions(self, request, queryset):
        count = 0
        with transaction.atomic():
            for revision in queryset.select_for_update().select_related("provider"):
                provider = Provider.objects.select_for_update().get(
                    pk=revision.provider_id
                )
                allowed = {"legal_name", "display_name", "y_tunnus", "provider_type"}
                for field, value in revision.payload.items():
                    if field in allowed:
                        setattr(provider, field, value)
                provider.claim_status = Provider.ClaimStatus.APPROVED
                provider.lifecycle = Provider.Lifecycle.PUBLISHED
                provider.save()
                revision.status = ProfileRevision.Status.APPROVED
                revision.reviewed_at = timezone.now()
                revision.save(update_fields=("status", "reviewed_at"))
                ProfileRevision.objects.filter(
                    provider=provider,
                    status=ProfileRevision.Status.APPROVED,
                ).exclude(pk=revision.pk).update(status=ProfileRevision.Status.SUPERSEDED)
                AuditEvent.objects.create(
                    provider=provider,
                    actor=request.user,
                    action="profile_revision.approved",
                    metadata={"revision_id": str(revision.pk)},
                )
                count += 1
        self.message_user(request, f"Approved {count} revision(s).")

    @admin.action(description="Request changes for selected revisions")
    def request_revision_changes(self, request, queryset):
        count = 0
        with transaction.atomic():
            for revision in queryset.select_for_update().select_related("provider"):
                revision.status = ProfileRevision.Status.CHANGES_REQUESTED
                revision.reviewed_at = timezone.now()
                revision.save(update_fields=("status", "reviewed_at"))
                revision.provider.lifecycle = Provider.Lifecycle.CHANGES_REQUESTED
                revision.provider.save(update_fields=("lifecycle", "updated_at"))
                AuditEvent.objects.create(
                    provider=revision.provider,
                    actor=request.user,
                    action="profile_revision.changes_requested",
                    metadata={"revision_id": str(revision.pk)},
                )
                count += 1
        self.message_user(request, f"Requested changes for {count} revision(s).")
