# P1-18 — Admin permission tests

Status: complete.

## Scope

Close the remaining P1 gate for Django admin permission boundaries without starting P2 work.

## Completed

- Non-staff users are denied access to Django admin.
- Staff without Provider model permissions cannot access Provider changelist or import.
- View-only Provider staff can inspect records but cannot run moderation or merge actions.
- Provider moderation and duplicate-merge actions explicitly require `change_provider` permission.
- Provider import requires `add_provider` permission.
- Moderation audit admin remains staff-readable and cannot add or delete audit records.

## Verification

Covered by `palvelut.apps.providers.test_admin_permissions.AdminPermissionTests` and the repository CI gates for the exact PR head.
