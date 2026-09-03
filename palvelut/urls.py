from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path

from palvelut.views import health_live, health_ready, localized_home, public_mount_root

urlpatterns = [
    path("palvelut/health/live", health_live, name="health-live"),
    path("palvelut/health/ready", health_ready, name="health-ready"),
    path("palvelut/staff/", admin.site.urls),
    path("palvelut/", public_mount_root, name="public-mount-root"),
    path("palvelut/<str:locale>/", localized_home, name="localized-home"),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
