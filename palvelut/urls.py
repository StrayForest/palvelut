from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

from palvelut.apps.discovery.contact import contact_redirect
from palvelut.apps.discovery.views import city_category, home, provider_profile, search
from palvelut.views import health_live, health_ready, public_mount_root

urlpatterns = [
    path("palvelut/health/live", health_live, name="health-live"),
    path("palvelut/health/ready", health_ready, name="health-ready"),
    path("palvelut/", public_mount_root, name="public-mount-root"),
    path("palvelut/<str:locale>/", home, name="localized-home"),
    path("palvelut/<str:locale>/search/", search, name="discovery-search"),
    path(
        "palvelut/<str:locale>/professionals/<slug:slug>/",
        provider_profile,
        name="provider-profile",
    ),
    path(
        "palvelut/<str:locale>/go/<uuid:provider_id>/<str:channel>/",
        contact_redirect,
        name="contact-redirect",
    ),
    path(
        "palvelut/<str:locale>/<slug:city>/<slug:category>/",
        city_category,
        name="city-category",
    ),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
