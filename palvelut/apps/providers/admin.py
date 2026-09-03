from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpRequest

from palvelut.apps.moderation.services import moderate_provider
from palvelut.apps.providers.models import (
    ContactChannel,
    MediaAsset,
    Provider,
    ProviderLanguage,
    ProviderMembership,
    ProviderService,
    ServiceArea,
)


class ProviderMembershipInline(admin.TabularInline):
    model = ProviderMembership
    extra = 0


class ProviderServiceInline(admin.TabularInline):
    model = ProviderService
    extra = 0


class ServiceAreaInline(admin.TabularInline):
    model = ServiceArea
    extra = 0


class ProviderLanguageInline(admin.TabularInline):
    model = ProviderLanguage
    extra = 0


class ContactChannelInline(admin.TabularInline):
    model = ContactChannel
    extra = 0


class MediaAssetInline(admin.TabularInline):
    model = MediaAsset
    extra = 0


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "provider_type",
        "lifecycle",
        "claim_status",
        "y_tunnus",
        "updated_at",
    )
    list_filter = ("provider_type", "lifecycle", "claim_status")
    search_fields = ("display_name", "legal_name", "y_tunnus")
    readonly_fields = ("lifecycle", "created_at", "updated_at")
    inlines = (
        ProviderMembershipInline,
        ProviderServiceInline,
        ServiceAreaInline,
        ProviderLanguageInline,
        ContactChannelInline,
        MediaAssetInline,
    )
    actions = ("approve_selected", "request_changes_selected", "suspend_selected")

    def save_model(
        self,
        request: HttpRequest,
        obj: Provider,
        form: object,
        change: bool,
    ) -> None:
        if not change:
            obj.lifecycle = Provider.Lifecycle.UNCLAIMED
        super().save_model(request, obj, form, change)

    def _run_action(self, request: HttpRequest, queryset, action: str) -> None:
        completed = 0
        for provider in queryset:
            try:
                moderate_provider(provider_id=provider.pk, actor=request.user, action=action)
            except ValidationError as exc:
                self.message_user(
                    request,
                    f"{provider}: {exc.message}",
                    level=messages.ERROR,
                )
            else:
                completed += 1
        if completed:
            self.message_user(request, f"Updated {completed} provider(s).")

    @admin.action(description="Approve and publish selected providers")
    def approve_selected(self, request: HttpRequest, queryset) -> None:
        self._run_action(request, queryset, "approve")

    @admin.action(description="Request changes for selected providers")
    def request_changes_selected(self, request: HttpRequest, queryset) -> None:
        self._run_action(request, queryset, "request_changes")

    @admin.action(description="Suspend selected providers")
    def suspend_selected(self, request: HttpRequest, queryset) -> None:
        self._run_action(request, queryset, "suspend")
