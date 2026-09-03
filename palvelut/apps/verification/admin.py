from django.contrib import admin

from .models import ProviderClaim, VerificationCheck
from .services import approve_claim, reject_claim


@admin.register(ProviderClaim)
class ProviderClaimAdmin(admin.ModelAdmin):
    list_display = (
        "provider",
        "claimed_by",
        "status",
        "created_at",
        "reviewed_by",
        "reviewed_at",
    )
    list_filter = ("status",)
    search_fields = (
        "provider__display_name",
        "provider__legal_name",
        "claimed_by__username",
    )
    readonly_fields = ("created_at", "reviewed_at")
    actions = ("approve_selected", "reject_selected")

    @admin.action(description="Approve selected claims")
    def approve_selected(self, request, queryset):  # type: ignore[no-untyped-def]
        for claim in queryset:
            approve_claim(claim=claim, actor=request.user)

    @admin.action(description="Reject selected claims")
    def reject_selected(self, request, queryset):  # type: ignore[no-untyped-def]
        for claim in queryset:
            reject_claim(claim=claim, actor=request.user)


@admin.register(VerificationCheck)
class VerificationCheckAdmin(admin.ModelAdmin):
    list_display = (
        "provider",
        "kind",
        "status",
        "checked_by",
        "checked_at",
        "expires_at",
    )
    list_filter = ("status", "kind")
    search_fields = (
        "provider__display_name",
        "provider__legal_name",
        "source_url",
    )
    readonly_fields = ("checked_at",)
