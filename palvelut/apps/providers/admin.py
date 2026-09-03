from django import forms
from django.contrib import admin, messages

from palvelut.apps.publishing.services import merge_duplicate, suspend_provider

from .models import (
    ContactChannel,
    MediaAsset,
    Provider,
    ProviderLanguage,
    ProviderMembership,
    ProviderService,
    ServiceArea,
)


class ProviderAdminForm(forms.ModelForm):
    imported = forms.BooleanField(
        required=False,
        help_text="Imported records stay unclaimed until an approved claim transition.",
    )

    class Meta:
        model = Provider
        fields = ("provider_type", "legal_name", "display_name", "y_tunnus")


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
    form = ProviderAdminForm
    list_display = (
        "display_name",
        "provider_type",
        "lifecycle",
        "y_tunnus",
        "updated_at",
    )
    list_filter = ("provider_type", "lifecycle")
    search_fields = ("display_name", "legal_name", "y_tunnus")
    readonly_fields = ("lifecycle", "created_at", "updated_at")
    actions = ("suspend_selected", "merge_selected_into_oldest")
    inlines = (
        ProviderMembershipInline,
        ProviderServiceInline,
        ServiceAreaInline,
        ProviderLanguageInline,
        ContactChannelInline,
        MediaAssetInline,
    )

    def save_model(self, request, obj, form, change):  # type: ignore[no-untyped-def]
        if not change:
            obj.lifecycle = (
                Provider.Lifecycle.UNCLAIMED
                if form.cleaned_data.get("imported")
                else Provider.Lifecycle.DRAFT
            )
        super().save_model(request, obj, form, change)

    @admin.action(description="Suspend selected providers")
    def suspend_selected(self, request, queryset):  # type: ignore[no-untyped-def]
        for provider in queryset:
            suspend_provider(provider=provider, actor=request.user)

    @admin.action(description="Merge selected duplicates into the oldest provider")
    def merge_selected_into_oldest(
        self, request, queryset
    ):  # type: ignore[no-untyped-def]
        providers = list(queryset.order_by("created_at", "id"))
        if len(providers) < 2:
            self.message_user(
                request,
                "Select at least two providers.",
                level=messages.ERROR,
            )
            return
        target = providers[0]
        for source in providers[1:]:
            merge_duplicate(source=source, target=target, actor=request.user)
        self.message_user(
            request,
            (
                f"Archived {len(providers) - 1} duplicate provider(s); "
                f"canonical provider is {target}."
            ),
            level=messages.SUCCESS,
        )
