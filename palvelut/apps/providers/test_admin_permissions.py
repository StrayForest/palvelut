from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory, TestCase
from django.urls import reverse

from palvelut.apps.moderation.admin import AuditEventAdmin
from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.admin import ProviderAdmin
from palvelut.apps.providers.models import Provider


class AdminPermissionTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.non_staff = user_model.objects.create_user(
            username="non-staff-admin-test",
            password="test-only-password",
        )
        self.staff = user_model.objects.create_user(
            username="staff-admin-test",
            password="test-only-password",
            is_staff=True,
        )
        self.factory = RequestFactory()
        self.provider_admin = ProviderAdmin(Provider, admin.site)

    def _grant_provider_permission(self, codename: str) -> None:
        content_type = ContentType.objects.get_for_model(Provider)
        permission = Permission.objects.get(
            content_type=content_type,
            codename=codename,
        )
        self.staff.user_permissions.add(permission)
        self.staff = get_user_model().objects.get(pk=self.staff.pk)

    def _request_for_staff(self):
        request = self.factory.get("/admin/providers/provider/")
        request.user = self.staff
        return request

    def test_non_staff_cannot_enter_admin(self) -> None:
        self.client.force_login(self.non_staff)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)

    def test_staff_without_provider_permissions_is_denied(self) -> None:
        self.client.force_login(self.staff)

        changelist = self.client.get(reverse("admin:providers_provider_changelist"))
        import_page = self.client.get(reverse("admin:providers_provider_import"))

        self.assertEqual(changelist.status_code, 403)
        self.assertEqual(import_page.status_code, 403)

    def test_view_only_staff_has_no_mutating_actions(self) -> None:
        self._grant_provider_permission("view_provider")
        request = self._request_for_staff()

        self.assertTrue(self.provider_admin.has_view_permission(request))
        self.assertFalse(self.provider_admin.has_change_permission(request))
        self.assertEqual(self.provider_admin.get_actions(request), {})

    def test_change_permission_exposes_guarded_actions(self) -> None:
        self._grant_provider_permission("view_provider")
        self._grant_provider_permission("change_provider")
        request = self._request_for_staff()

        actions = self.provider_admin.get_actions(request)

        self.assertEqual(
            set(actions),
            {
                "approve_selected",
                "request_changes_selected",
                "suspend_selected",
                "merge_duplicates",
            },
        )

    def test_import_requires_add_provider_permission(self) -> None:
        self.client.force_login(self.staff)
        self._grant_provider_permission("add_provider")
        self.client.force_login(self.staff)

        response = self.client.get(reverse("admin:providers_provider_import"))

        self.assertEqual(response.status_code, 200)

    def test_audit_admin_is_read_only_and_staff_only(self) -> None:
        model_admin = AuditEventAdmin(AuditEvent, admin.site)
        non_staff_request = self.factory.get("/admin/moderation/auditevent/")
        non_staff_request.user = self.non_staff
        staff_request = self.factory.get("/admin/moderation/auditevent/")
        staff_request.user = self.staff

        self.assertFalse(model_admin.has_add_permission(staff_request))
        self.assertFalse(model_admin.has_delete_permission(staff_request))
        self.assertFalse(model_admin.has_change_permission(non_staff_request))
        self.assertTrue(model_admin.has_change_permission(staff_request))
