from __future__ import annotations

from django.contrib import admin, messages
from django.db import transaction

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import (
    ContactChannel,
    MediaAsset,
    Provider,
    ProviderLanguage,
    ProviderMembership,
    ProviderService,
    ServiceArea,
)


def _audit(provider: Provider, actor, action: str, **metadata: object) -> None:
    AuditEvent.objects.create(
        provider=provider,
        actor=actor,
        action=action,
        metadata=metadata,
    )


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("display_name", "provider_type", "lifecycle", "claim_status", "y_tunnus", "updated_at")
    list_filter = ("provider_type", "lifecycle", "claim_status")
    search_fields = ("display_name", "legal_name", "y_tunnus")
    readonly_fields = ("created_at", "updated_at")
    actions = ("approve_selected", "request_changes", "suspend_selected", "merge_duplicates")

    @admin.action(description="Approve selected providers")
    def approve_selected(self, request, queryset):
        count = 0
        with transaction.atomic():
            for provider in queryset.select_for_update():
                provider.claim_status = Provider.ClaimStatus.APPROVED
                provider.lifecycle = Provider.Lifecycle.PUBLISHED
                provider.save(update_fields=("claim_status", "lifecycle", "updated_at"))
                _audit(provider, request.user, "provider.approved")
                count += 1
        self.message_user(request, f"Approved {count} provider(s).")

    @admin.action(description="Request changes for selected providers")
    def request_changes(self, request, queryset):
        count = 0
        with transaction.atomic():
            for provider in queryset.select_for_update():
                provider.lifecycle = Provider.Lifecycle.CHANGES_REQUESTED
                provider.save(update_fields=("lifecycle", "updated_at"))
                _audit(provider, request.user, "provider.changes_requested")
                count += 1
        self.message_user(request, f"Requested changes for {count} provider(s).")

    @admin.action(description="Suspend selected providers")
    def suspend_selected(self, request, queryset):
        count = 0
        with transaction.atomic():
            for provider in queryset.select_for_update():
                provider.lifecycle = Provider.Lifecycle.SUSPENDED
                provider.save(update_fields=("lifecycle", "updated_at"))
                _audit(provider, request.user, "provider.suspended")
                count += 1
        self.message_user(request, f"Suspended {count} provider(s).")

    @admin.action(description="Merge exactly two duplicate providers")
    def merge_duplicates(self, request, queryset):
        providers = list(queryset.order_by("created_at", "id")[:3])
        if len(providers) != 2:
            self.message_user(
                request,
                "Select exactly two providers. The oldest record is kept as canonical.",
                level=messages.ERROR,
            )
            return

        target, duplicate = providers
        with transaction.atomic():
            target = Provider.objects.select_for_update().get(pk=target.pk)
            duplicate = Provider.objects.select_for_update().get(pk=duplicate.pk)
            related_models = (
                (ProviderService, "provider"),
                (ServiceArea, "provider"),
                (ProviderLanguage, "provider"),
                (ContactChannel, "provider"),
                (MediaAsset, "provider"),
            )
            for model, field in related_models:
                for item in model.objects.filter(provider=duplicate):
                    setattr(item, field, target)
                    try:
                        item.save()
                    except Exception:
                        item.delete()

            ProviderMembership.objects.filter(provider=duplicate).update(is_active=False)
            duplicate.lifecycle = Provider.Lifecycle.ARCHIVED
            duplicate.save(update_fields=("lifecycle", "updated_at"))
            _audit(
                target,
                request.user,
                "provider.duplicates_merged",
                duplicate_provider_id=str(duplicate.pk),
            )
            _audit(
                duplicate,
                request.user,
                "provider.merged_into",
                canonical_provider_id=str(target.pk),
            )

        self.message_user(
            request,
            f"Merged {duplicate.display_name} into {target.display_name}.",
        )


@admin.register(ProviderMembership)
class ProviderMembershipAdmin(admin.ModelAdmin):
    list_display = ("provider", "account", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    autocomplete_fields = ("provider", "account")


for model in (ProviderService, ServiceArea, ProviderLanguage, ContactChannel, MediaAsset):
    admin.site.register(model)
