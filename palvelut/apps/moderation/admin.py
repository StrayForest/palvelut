from django.contrib import admin

from palvelut.apps.moderation.models import (
    AuditEvent,
    ContentReport,
    ModerationAppeal,
    ModerationCase,
    ModerationEvent,
    ProviderNotice,
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
        "reason",
        "status",
        "opened_by",
        "opened_at",
        "closed_at",
    )
    list_filter = ("status",)
    search_fields = ("provider__display_name", "reason")


@admin.register(ModerationEvent)
class ModerationEventAdmin(ReadOnlyAdmin):
    list_display = ("case", "event_type", "actor", "created_at")
    search_fields = ("case__provider__display_name", "event_type", "actor__username")


@admin.register(ContentReport)
class ContentReportAdmin(ReadOnlyAdmin):
    list_display = ("case", "created_at")
    search_fields = ("case__provider__display_name", "case__reason")


@admin.register(ProviderNotice)
class ProviderNoticeAdmin(ReadOnlyAdmin):
    list_display = ("case", "created_by", "created_at")
    search_fields = ("case__provider__display_name", "created_by__username")


@admin.register(ModerationAppeal)
class ModerationAppealAdmin(ReadOnlyAdmin):
    list_display = ("case", "submitted_by", "status", "created_at", "reviewed_at")
    list_filter = ("status",)
    search_fields = ("case__provider__display_name", "submitted_by__username")
