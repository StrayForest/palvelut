from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

from palvelut.apps.accounts.views import (
    account_home,
    account_login,
    account_logout,
    password_reset_confirm,
    password_reset_request,
    register,
    staff_mfa,
    staff_mfa_setup,
    verify_email,
)
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
from palvelut.views import health_live, health_ready, public_mount_root

cached_home = public_read_through_cache(
    namespace="home-v1",
    application_ttl=3600,
    shared_max_age=3600,
    stale_while_revalidate=3600,
)(home)
cached_search = public_read_through_cache(
    namespace="search-v1",
    application_ttl=120,
    shared_max_age=None,
)(search)
cached_profile = public_read_through_cache(
    namespace="profile-v1",
    application_ttl=300,
    shared_max_age=300,
    stale_while_revalidate=86400,
)(provider_profile)
cached_city_category = public_read_through_cache(
    namespace="city-category-v1",
    application_ttl=300,
    shared_max_age=300,
    stale_while_revalidate=86400,
)(city_category)

urlpatterns = [
    path("palvelut/health/live", health_live, name="health-live"),
    path("palvelut/health/ready", health_ready, name="health-ready"),
    path("palvelut/robots.txt", robots_txt, name="robots-txt"),
    path("palvelut/sitemap.xml", sitemap_xml, name="sitemap-xml"),
    path("palvelut/", public_mount_root, name="public-mount-root"),
    path("palvelut/<str:locale>/", cached_home, name="localized-home"),
    path("palvelut/<str:locale>/search/", cached_search, name="discovery-search"),
    path("palvelut/<str:locale>/account/", account_home, name="account-home"),
    path("palvelut/<str:locale>/account/register/", register, name="account-register"),
    path("palvelut/<str:locale>/account/login/", account_login, name="account-login"),
    path("palvelut/<str:locale>/account/logout/", account_logout, name="account-logout"),
    path("palvelut/<str:locale>/account/mfa/", staff_mfa, name="account-mfa"),
    path("palvelut/<str:locale>/account/mfa/setup/", staff_mfa_setup, name="account-mfa-setup"),
    path(
        "palvelut/<str:locale>/account/verify/<uidb64>/<token>/",
        verify_email,
        name="account-verify",
    ),
    path(
        "palvelut/<str:locale>/account/password-reset/",
        password_reset_request,
        name="account-password-reset",
    ),
    path(
        "palvelut/<str:locale>/account/password-reset/<uidb64>/<token>/",
        password_reset_confirm,
        name="account-password-reset-confirm",
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
