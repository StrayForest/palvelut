from django.urls import path

from palvelut.views import localized_home

urlpatterns = [
    path("palvelut/<str:locale>/", localized_home, name="localized-home"),
]
