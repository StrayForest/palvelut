from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

from palvelut.apps.accounts.views import (
    ProviderLoginView,
    ProviderLogoutView,
    SecurePasswordResetCompleteView,
    SecurePasswordResetConfirmView,
    SecurePasswordResetDoneView,
    SecurePasswordResetView,
    register,
    staff_mfa,
    verify_email,
)
from palvelut.apps.analytics.services import track_provider_events
from palvelut.apps.content.views import legal_document
from palvelut.apps.discovery.cache import public_read_through_cache
from palvelut.apps.discovery.contact import contact_redirect
from palvelut.apps.discovery.views import (
    city_category,
    home,
    provider_profile,
    robots_txt,
    search,
    sitemap_xml,
)
from palvelut.apps.moderation.data_rights_views import (
    data_subject_requests,
    staff_data_subject_request_detail,
    staff_data_subject_request_list,
)
from palvelut.apps.moderation.views import (
    provider_case_detail,
    provider_case_list,
    report_provider,
    report_status,
    staff_case_detail,
    staff_case_list,
)
from palvelut.apps.providers.claim_views import (
    claim_candidates,
    claim_provider,
    staff_claim_list,
    staff_claim_review,
)
from palvelut.apps.providers.workspace_views import (
    edit_profile,
    preview_profile,
    submit_profile,
    upload_profile_media,
    workspace,
)
from palvelut.apps.verification.views import trust
from palvelut.views import health_live, health_ready, public_mount_root

cached_home = public_read_through_cache(
    namespace="home-v1",
    application_ttl=3600,
    shared_max_age=3600,
    stale_while_revalidate=3600,
)(home)
cached_search = track_provider_events("impression")(
    public_read_through_cache(
        namespace="search-v1",
        application_ttl=120,
        shared_max_age=None,
    )(search)
)
cached_profile = track_provider_events("profile_view")(
    public_read_through_cache(
        namespace="profile-v1",
        application_ttl=300,
        shared_max_age=300,
        stale_while_revalidate=86400,
    )(provider_profile)
)
cached_city_category = track_provider_events("impression")(
    public_read_through_cache(
        namespace="city-category-v1",
        application_ttl=300,
        shared_max_age=300,
        stale_while_revalidate=86400,
    )(city_category)
)
cached_trust = public_read_through_cache(
    namespace="trust-v1",
    application_ttl=3600,
    shared_max_age=3600,
    stale_while_revalidate=86400,
)(trust)

urlpatterns = [
    path("palvelut/health/live", health_live, name="health-live"),
    path("palvelut/health/ready", health_ready, name="health-ready"),
    path("palvelut/robots.txt", robots_txt, name="robots-txt"),
    path("palvelut/sitemap.xml", sitemap_xml, name="sitemap-xml"),
    path("palvelut/account/register/", register, name="account-register"),
    path(
        "palvelut/account/verify/<str:token>/",
        verify_email,
        name="account-verify-email",
    ),
    path("palvelut/account/login/", ProviderLoginView.as_view(), name="account-login"),
    path(
        "palvelut/account/logout/", ProviderLogoutView.as_view(), name="account-logout"
    ),
    path(
        "palvelut/account/password-reset/",
        SecurePasswordResetView.as_view(),
        name="account-password-reset",
    ),
    path(
        "palvelut/account/password-reset/done/",
        SecurePasswordResetDoneView.as_view(),
        name="account-password-reset-done",
    ),
    path(
        "palvelut/account/password-reset/<uidb64>/<token>/",
        SecurePasswordResetConfirmView.as_view(),
        name="account-password-reset-confirm",
    ),
    path(
        "palvelut/account/password-reset/complete/",
        SecurePasswordResetCompleteView.as_view(),
        name="account-password-reset-complete",
    ),
    path("palvelut/account/mfa/", staff_mfa, name="staff-mfa"),
    path("palvelut/account/claims/", claim_candidates, name="account-claim-list"),
    path(
        "palvelut/account/claims/<uuid:provider_id>/",
        claim_provider,
        name="account-claim-provider",
    ),
    path(
        "palvelut/account/data-rights/",
        data_subject_requests,
        name="data-subject-requests",
    ),
    path("palvelut/account/profile/", workspace, name="provider-workspace"),
    path(
        "palvelut/account/profile/<uuid:provider_id>/",
        edit_profile,
        name="provider-workspace-edit",
    ),
    path(
        "palvelut/account/profile/<uuid:provider_id>/media/",
        upload_profile_media,
        name="provider-workspace-media-upload",
    ),
    path(
        "palvelut/account/profile/<uuid:provider_id>/preview/",
        preview_profile,
        name="provider-workspace-preview",
    ),
    path(
        "palvelut/account/profile/<uuid:provider_id>/submit/",
        submit_profile,
        name="provider-workspace-submit",
    ),
    path(
        "palvelut/account/content-cases/",
        provider_case_list,
        name="provider-content-case-list",
    ),
    path(
        "palvelut/account/content-cases/<uuid:case_id>/",
        provider_case_detail,
        name="provider-content-case-detail",
    ),
    path(
        "palvelut/report/status/<uuid:case_id>/",
        report_status,
        name="content-report-status",
    ),
    path("palvelut/staff/claims/", staff_claim_list, name="staff-claim-list"),
    path(
        "palvelut/staff/claims/<uuid:provider_id>/",
        staff_claim_review,
        name="staff-claim-review",
    ),
    path(
        "palvelut/staff/content-cases/",
        staff_case_list,
        name="staff-content-case-list",
    ),
    path(
        "palvelut/staff/content-cases/<uuid:case_id>/",
        staff_case_detail,
        name="staff-content-case-detail",
    ),
    path(
        "palvelut/staff/data-rights/",
        staff_data_subject_request_list,
        name="staff-data-subject-request-list",
    ),
    path(
        "palvelut/staff/data-rights/<uuid:request_id>/",
        staff_data_subject_request_detail,
        name="staff-data-subject-request-detail",
    ),
    path("palvelut/staff/", admin.site.urls),
    path("palvelut/", public_mount_root, name="public-mount-root"),
    path("palvelut/<str:locale>/", cached_home, name="localized-home"),
    path("palvelut/<str:locale>/search/", cached_search, name="discovery-search"),
    path("palvelut/<str:locale>/trust/", cached_trust, name="trust"),
    path(
        "palvelut/<str:locale>/legal/<str:document>/",
        legal_document,
        name="legal-document",
    ),
    path(
        "palvelut/<str:locale>/report/<slug:slug>/",
        report_provider,
        name="content-report-provider",
    ),
    path(
        "palvelut/<str:locale>/professionals/<slug:slug>/",
        cached_profile,
        name="provider-profile",
    ),
    path(
        "palvelut/<str:locale>/go/<uuid:provider_id>/<str:channel>/",
        contact_redirect,
        name="contact-redirect",
    ),
    path(
        "palvelut/<str:locale>/<slug:city>/<slug:category>/",
        cached_city_category,
        name="city-category",
    ),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
