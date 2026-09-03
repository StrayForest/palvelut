import difflib
import json

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from .models import ProfileRevision
from .services import approve_revision, request_revision_changes


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
    readonly_fields = ("created_at", "reviewed_at", "revision_diff")
    actions = ("approve_selected", "request_changes_selected")

    @admin.display(description="Diff against latest approved revision")
    def revision_diff(self, obj: ProfileRevision) -> str:
        if not obj.pk:
            return "Save the revision to calculate a diff."
        previous = (
            ProfileRevision.objects.filter(
                provider=obj.provider,
                status=ProfileRevision.Status.APPROVED,
            )
            .exclude(pk=obj.pk)
            .order_by("-created_at", "-id")
            .first()
        )
        before = json.dumps(
            previous.payload if previous else {}, indent=2, sort_keys=True
        ).splitlines()
        after = json.dumps(obj.payload, indent=2, sort_keys=True).splitlines()
        diff = "\n".join(
            difflib.unified_diff(
                before,
                after,
                fromfile="approved",
                tofile="candidate",
                lineterm="",
            )
        )
        return format_html("<pre>{}</pre>", diff or "No changes")

    @admin.action(description="Approve selected revisions")
    def approve_selected(self, request, queryset):  # type: ignore[no-untyped-def]
        approved = 0
        for revision in queryset:
            try:
                approve_revision(revision=revision, actor=request.user)
            except ValidationError as exc:
                self.message_user(
                    request,
                    f"{revision}: {exc.message}",
                    level=messages.ERROR,
                )
            else:
                approved += 1
        if approved:
            self.message_user(
                request,
                f"Approved {approved} revision(s).",
                level=messages.SUCCESS,
            )

    @admin.action(description="Request changes for selected revisions")
    def request_changes_selected(
        self, request, queryset
    ):  # type: ignore[no-untyped-def]
        for revision in queryset:
            request_revision_changes(revision=revision, actor=request.user)
