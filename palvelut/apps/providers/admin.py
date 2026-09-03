from __future__ import annotations

from django import forms
from django.contrib import admin, messages
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse

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


class ProviderImportForm(forms.Form):
    records = forms.JSONField(
        help_text=(
            "JSON array of provider objects. Required: provider_type, legal_name, "
            "display_name."
        )
    )

    def clean_records(self):
        records = self.cleaned_data["records"]
        if not isinstance(records, list) or not records:
            raise forms.ValidationError("Provide a non-empty JSON array.")
        required = {"provider_type", "legal_name", "display_name"}
        for index, record in enumerate(records):
            if not isinstance(record, dict) or not required.issubset(record):
                raise forms.ValidationError(
                    f"Record {index + 1} must contain provider_type, legal_name and display_name."
                )
            if record["provider_type"] not in Provider.Type.values:
                raise forms.ValidationError(
                    f"Record {index + 1} has an invalid provider_type."
                )
        return records


def _audit(provider: Provider, actor, action: str, **metadata: object) -> None:
    AuditEvent.objects.create(
        provider=provider,
        actor=actor,
        action=action,
        metadata=metadata,
    )


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    change_list_template = "admin/providers/provider/change_list.html"
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
    readonly_fields = ("created_at", "updated_at")
    actions = (
        "approve_selected",
        "request_changes",
        "suspend_selected",
        "merge_duplicates",
    )

    def get_urls(self):
        return [
            path(
                "import/",
                self.admin_site.admin_view(self.import_view),
                name="providers_provider_import",
            ),
            *super().get_urls(),
        ]

    def import_view(self, request: HttpRequest) -> HttpResponse:
        if not self.has_add_permission(request):
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied
        form = ProviderImportForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            created = 0
            updated = 0
            with transaction.atomic():
                for record in form.cleaned_data["records"]:
                    y_tunnus = str(record.get("y_tunnus", "")).strip()
                    defaults = {
                        "provider_type": record["provider_type"],
                        "legal_name": str(record["legal_name"]).strip(),
                        "display_name": str(record["display_name"]).strip(),
                    }
                    if y_tunnus:
                        provider, was_created = Provider.objects.update_or_create(
                            y_tunnus=y_tunnus,
                            defaults=defaults,
                        )
                    else:
                        provider, was_created = Provider.objects.get_or_create(
                            y_tunnus="",
                            **defaults,
                        )
                    _audit(
                        provider,
                        request.user,
                        "provider.imported",
                        created=was_created,
                    )
                    created += int(was_created)
                    updated += int(not was_created)
            self.message_user(
                request,
                f"Import complete: {created} created, {updated} updated.",
            )
            return redirect(reverse("admin:providers_provider_changelist"))
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Import providers",
            "form": form,
        }
        return render(request, "admin/providers/provider/import.html", context)

    @admin.action(description="Approve selected providers")
    def approve_selected(self, request, queryset):
        count = 0
        with transaction.atomic():
            for provider in queryset.select_for_update():
                provider.claim_status = Provider.ClaimStatus.APPROVED
                provider.lifecycle = Provider.Lifecycle.PUBLISHED
                provider.save(
                    update_fields=("claim_status", "lifecycle", "updated_at")
                )
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
            models = (
                ProviderService,
                ServiceArea,
                ProviderLanguage,
                ContactChannel,
                MediaAsset,
            )
            for model in models:
                for item in model.objects.filter(provider=duplicate):
                    item.provider = target
                    try:
                        item.save()
                    except IntegrityError:
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


for model in (
    ProviderService,
    ServiceArea,
    ProviderLanguage,
    ContactChannel,
    MediaAsset,
):
    admin.site.register(model)
