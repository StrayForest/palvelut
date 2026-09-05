import difflib
import json

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from palvelut.apps.publishing.models import ProfileRevision
from palvelut.apps.publishing.workflow import approve_revision, request_revision_changes


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
    search_fields = (
        "provider__display_name",
        "provider__legal_name",
        "provider__y_tunnus",
    )
    actions = ("approve_selected", "request_changes_selected")

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return (
                "status",
                "created_by",
                "created_at",
                "reviewed_at",
                "revision_diff",
            )
        return (
            "provider",
            "status",
            "payload",
            "created_by",
            "created_at",
            "reviewed_at",
            "revision_diff",
        )

    @admin.display(description="Changes from previous revision")
    def revision_diff(self, obj: ProfileRevision | None) -> str:
        if obj is None or obj.pk is None:
            return format_html("<pre>{}</pre>", "New revision")
        previous = (
            ProfileRevision.objects.filter(
                provider=obj.provider,
                created_at__lt=obj.created_at,
            )
            .order_by("-created_at", "-id")
            .first()
        )
        before = json.dumps(
            previous.payload if previous else {},
            indent=2,
            sort_keys=True,
        ).splitlines()
        after = json.dumps(obj.payload, indent=2, sort_keys=True).splitlines()
        diff = "\n".join(
            difflib.unified_diff(
                before,
                after,
                fromfile="previous",
                tofile="current",
                lineterm="",
            )
        )
        return format_html("<pre>{}</pre>", diff or "No payload changes")

    @admin.action(description="Approve selected revisions")
    def approve_selected(self, request, queryset):
        for revision in queryset:
            try:
                approve_revision(revision_id=revision.pk, actor=request.user)
            except ValidationError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)

    @admin.action(description="Request corrections for selected revisions")
    def request_changes_selected(self, request, queryset):
        for revision in queryset:
            try:
                request_revision_changes(
                    revision_id=revision.pk,
                    actor=request.user,
                    note="Corrections requested by staff",
                )
            except ValidationError as exc:
                self.message_user(request, str(exc), level=messages.ERROR)

    def has_add_permission(self, request) -> bool:
        return bool(request.user.is_staff and super().has_add_permission(request))

    def save_model(self, request, obj, form, change) -> None:
        if not change:
            obj.created_by = request.user
            obj.status = ProfileRevision.Status.PENDING
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
