import json

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html

from palvelut.apps.moderation.models import AuditEvent, ModerationCase, ModerationEvent
from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.providers.services import merge_duplicate_pair, suspend_provider
from palvelut.apps.publishing.models import ProfileRevision
from palvelut.apps.publishing.services import (
    approve_revision,
    request_revision_changes,
    revision_diff,
)
from palvelut.apps.verification.models import ProviderClaim, VerificationCheck
from palvelut.apps.verification.services import approve_claim, reject_claim


class ProviderMembershipInline(admin.TabularInline):
    model = ProviderMembership
    extra = 0
    autocomplete_fields = ("account",)


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "provider_type",
        "lifecycle",
        "y_tunnus",
        "updated_at",
    )
    list_filter = ("provider_type", "lifecycle")
    search_fields = ("display_name", "legal_name", "y_tunnus")
    inlines = (ProviderMembershipInline,)
    actions = ("suspend_selected", "merge_selected_duplicate_pair")

    @admin.action(description="Suspend selected providers")
    def suspend_selected(
        self, request: HttpRequest, queryset: QuerySet[Provider]
    ) -> None:
        changed = 0
        for provider in queryset:
            try:
                suspend_provider(
                    provider=provider,
                    actor=request.user,
                    reason="Staff admin action",
                )
            except ValidationError as exc:
                self.message_user(
                    request, "; ".join(exc.messages), level=messages.ERROR
                )
            else:
                changed += 1
        if changed:
            self.message_user(
                request,
                f"Suspended {changed} provider(s).",
                level=messages.SUCCESS,
            )

    @admin.action(description="Merge exactly two duplicates (oldest UUIDv7 survives)")
    def merge_selected_duplicate_pair(
        self, request: HttpRequest, queryset: QuerySet[Provider]
    ) -> None:
        providers = list(queryset.order_by("id")[:3])
        if len(providers) != 2:
            self.message_user(
                request,
                "Select exactly two providers to merge.",
                level=messages.ERROR,
            )
            return
        try:
            survivor = merge_duplicate_pair(
                first=providers[0], second=providers[1], actor=request.user
            )
        except ValidationError as exc:
            self.message_user(request, "; ".join(exc.messages), level=messages.ERROR)
            return
        self.message_user(
            request,
            f"Merged duplicate into {survivor.display_name}.",
            level=messages.SUCCESS,
        )


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
    readonly_fields = ("created_at", "reviewed_at", "revision_diff_view")
    actions = ("approve_selected", "request_changes_selected")

    @admin.display(description="Diff against current approved revision")
    def revision_diff_view(self, obj: ProfileRevision | None) -> str:
        if obj is None or obj.pk is None:
            return "Save the revision to calculate a diff."
        rendered = json.dumps(
            revision_diff(obj), ensure_ascii=False, indent=2, sort_keys=True
        )
        return format_html("<pre>{}</pre>", rendered)

    @admin.action(description="Approve selected pending revisions")
    def approve_selected(
        self, request: HttpRequest, queryset: QuerySet[ProfileRevision]
    ) -> None:
        changed = 0
        for revision in queryset:
            try:
                approve_revision(revision=revision, actor=request.user)
            except ValidationError as exc:
                self.message_user(
                    request, "; ".join(exc.messages), level=messages.ERROR
                )
            else:
                changed += 1
        if changed:
            self.message_user(
                request,
                f"Approved {changed} revision(s).",
                level=messages.SUCCESS,
            )

    @admin.action(description="Request changes for selected pending revisions")
    def request_changes_selected(
        self, request: HttpRequest, queryset: QuerySet[ProfileRevision]
    ) -> None:
        changed = 0
        for revision in queryset:
            try:
                request_revision_changes(revision=revision, actor=request.user)
            except ValidationError as exc:
                self.message_user(
                    request, "; ".join(exc.messages), level=messages.ERROR
                )
            else:
                changed += 1
        if changed:
            self.message_user(
                request,
                f"Requested changes for {changed} revision(s).",
                level=messages.SUCCESS,
            )


@admin.register(ProviderClaim)
class ProviderClaimAdmin(admin.ModelAdmin):
    list_display = (
        "provider",
        "claimant",
        "status",
        "evidence_type",
        "requested_at",
        "reviewed_at",
    )
    list_filter = ("status", "evidence_type")
    search_fields = (
        "provider__display_name",
        "provider__legal_name",
        "claimant__username",
    )
    autocomplete_fields = ("provider", "claimant", "reviewed_by")
    readonly_fields = ("requested_at", "reviewed_at", "reviewed_by")
    actions = ("approve_selected", "reject_selected")

    @admin.action(description="Approve selected pending claims")
    def approve_selected(
        self, request: HttpRequest, queryset: QuerySet[ProviderClaim]
    ) -> None:
        changed = 0
        for claim in queryset:
            try:
                approve_claim(claim=claim, actor=request.user)
            except ValidationError as exc:
                self.message_user(
                    request, "; ".join(exc.messages), level=messages.ERROR
                )
            else:
                changed += 1
        if changed:
            self.message_user(
                request,
                f"Approved {changed} claim(s).",
                level=messages.SUCCESS,
            )

    @admin.action(description="Reject selected pending claims")
    def reject_selected(
        self, request: HttpRequest, queryset: QuerySet[ProviderClaim]
    ) -> None:
        changed = 0
        for claim in queryset:
            try:
                reject_claim(claim=claim, actor=request.user)
            except ValidationError as exc:
                self.message_user(
                    request, "; ".join(exc.messages), level=messages.ERROR
                )
            else:
                changed += 1
        if changed:
            self.message_user(
                request,
                f"Rejected {changed} claim(s).",
                level=messages.SUCCESS,
            )


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
    search_fields = ("provider__display_name", "provider__legal_name")
    autocomplete_fields = ("provider", "checked_by")


@admin.register(ModerationCase)
class ModerationCaseAdmin(admin.ModelAdmin):
    list_display = (
        "provider",
        "reason",
        "status",
        "opened_by",
        "opened_at",
        "closed_at",
    )
    list_filter = ("status",)
    search_fields = ("provider__display_name", "reason")
    autocomplete_fields = ("provider", "opened_by")


@admin.register(ModerationEvent)
class ModerationEventAdmin(admin.ModelAdmin):
    list_display = ("case", "event_type", "actor", "created_at")
    search_fields = ("case__provider__display_name", "event_type", "note")
    autocomplete_fields = ("case", "actor")
    readonly_fields = ("created_at",)


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "action", "actor", "created_at")
    list_filter = ("action",)
    search_fields = ("provider__display_name", "action")
    readonly_fields = ("provider", "actor", "action", "metadata", "created_at")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: AuditEvent | None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: AuditEvent | None = None
    ) -> bool:
        return False


admin.site.site_header = "Palvelut staff"
admin.site.site_title = "Palvelut staff"
admin.site.index_title = "Back office"
