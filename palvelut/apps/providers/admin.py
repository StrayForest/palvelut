from __future__ import annotations

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import path, reverse

from palvelut.apps.moderation.models import AuditEvent
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


class ProviderImportForm(forms.Form):
    records = forms.JSONField(
        help_text="JSON list. Required: provider_type, legal_name, display_name.",
    )

    def clean_records(self):
        records = self.cleaned_data["records"]
        if not isinstance(records, list) or not records:
            raise forms.ValidationError("Provide a non-empty JSON array.")
        required = {"provider_type", "legal_name", "display_name"}
        for index, record in enumerate(records):
            if not isinstance(record, dict) or not required.issubset(record):
                message = f"Record {index + 1} is missing required provider fields."
                raise forms.ValidationError(message)
            if record["provider_type"] not in Provider.Type.values:
                message = f"Record {index + 1} has an invalid provider_type."
                raise forms.ValidationError(message)
        return records


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
    readonly_fields = ("lifecycle", "created_at", "updated_at")
    inlines = (
        ProviderMembershipInline,
        ProviderServiceInline,
        ServiceAreaInline,
        ProviderLanguageInline,
        ContactChannelInline,
        MediaAssetInline,
    )
    actions = (
        "approve_selected",
        "request_changes_selected",
        "suspend_selected",
        "merge_duplicates",
    )

    def get_urls(self):
        custom_urls = [
            path(
                "import/",
                self.admin_site.admin_view(self.import_view),
                name="providers_provider_import",
            ),
        ]
        return [*custom_urls, *super().get_urls()]

    def import_view(self, request: HttpRequest) -> HttpResponse:
        if not self.has_add_permission(request):
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
        if not change:
            _audit(obj, request.user, "provider.created")

    def _run_action(self, request: HttpRequest, queryset, action: str) -> None:
        completed = 0
        for provider in queryset:
            try:
                moderate_provider(
                    provider_id=provider.pk,
                    actor=request.user,
                    action=action,
                )
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

    @admin.action(
        description="Approve and publish selected providers",
        permissions=["change"],
    )
    def approve_selected(self, request: HttpRequest, queryset) -> None:
        self._run_action(request, queryset, "approve")

    @admin.action(
        description="Request changes for selected providers",
        permissions=["change"],
    )
    def request_changes_selected(self, request: HttpRequest, queryset) -> None:
        self._run_action(request, queryset, "request_changes")

    @admin.action(description="Suspend selected providers", permissions=["change"])
    def suspend_selected(self, request: HttpRequest, queryset) -> None:
        self._run_action(request, queryset, "suspend")

    @admin.action(
        description="Merge exactly two duplicate providers",
        permissions=["change"],
    )
    def merge_duplicates(self, request: HttpRequest, queryset) -> None:
        providers = list(queryset.order_by("created_at", "id")[:3])
        if len(providers) != 2:
            self.message_user(
                request,
                "Select exactly two providers; the oldest is canonical.",
                level=messages.ERROR,
            )
            return

        target, duplicate = providers
        with transaction.atomic():
            target = Provider.objects.select_for_update().get(pk=target.pk)
            duplicate = Provider.objects.select_for_update().get(pk=duplicate.pk)
            related_models = (
                ProviderService,
                ServiceArea,
                ProviderLanguage,
                ContactChannel,
                MediaAsset,
            )
            for model in related_models:
                for item in model.objects.filter(provider=duplicate):
                    item.provider = target
                    try:
                        with transaction.atomic():
                            item.save()
                    except IntegrityError:
                        item.delete()

            ProviderMembership.objects.filter(provider=duplicate).update(
                is_active=False,
            )
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
