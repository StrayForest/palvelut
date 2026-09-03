import difflib
import json

from django.contrib import admin
from django.utils.html import format_html

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
    search_fields = (
        "provider__display_name",
        "provider__legal_name",
        "provider__y_tunnus",
    )
    readonly_fields = (
        "provider",
        "status",
        "payload",
        "created_by",
        "created_at",
        "reviewed_at",
        "revision_diff",
    )

    @admin.display(description="Changes from previous revision")
    def revision_diff(self, obj: ProfileRevision) -> str:
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

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
