from django.contrib import admin

from palvelut.apps.moderation.models import (
    AuditEvent,
    ContentReport,
    ModerationCase,
    ModerationEvent,
)


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)


@admin.register(AuditEvent)
class AuditEventAdmin(ReadOnlyAdmin):
    list_display = ("action", "provider", "actor", "created_at")
    list_filter = ("action",)
    search_fields = ("provider__display_name", "actor__username", "action")


@admin.register(ModerationCase)
class ModerationCaseAdmin(ReadOnlyAdmin):
    list_display = (
        "provider",
        "kind",
        "reason",
        "status",
        "opened_by",
        "opened_at",
        "closed_at",
    )
    list_filter = ("kind", "status")
    search_fields = ("provider__display_name", "reason")


@admin.register(ContentReport)
class ContentReportAdmin(ReadOnlyAdmin):
    list_display = ("case", "category", "created_at")
    list_filter = ("category",)
    search_fields = ("case__provider__display_name", "category")


@admin.register(ModerationEvent)
class ModerationEventAdmin(ReadOnlyAdmin):
    list_display = (
        "case",
        "event_type",
        "actor",
        "visible_to_provider",
        "created_at",
    )
    list_filter = ("visible_to_provider", "event_type")
    search_fields = ("case__provider__display_name", "event_type", "actor__username")
