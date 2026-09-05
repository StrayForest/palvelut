from django.apps import AppConfig


class ProvidersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "palvelut.apps.providers"

    def ready(self) -> None:
        from . import access_audit, team_models  # noqa: F401
