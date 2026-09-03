from django.urls import path

from palvelut.views import localized_home, public_mount_root

urlpatterns = [
    path("palvelut/", public_mount_root, name="public-mount-root"),
    path("palvelut/<str:locale>/", localized_home, name="localized-home"),
]
