from pathlib import Path


SETTINGS = Path("palvelut/settings.py")
PRODUCTION_COMPOSE = Path("compose.production.yml")
ENV_EXAMPLE = Path(".env.example")


def test_settings_support_optional_email_delivery_and_future_smtp() -> None:
    settings = SETTINGS.read_text()

    assert '"EMAIL_DELIVERY_ENABLED", ENVIRONMENT in {"local", "test"}' in settings
    assert '"ACCOUNT_EMAIL_VERIFICATION_REQUIRED", EMAIL_DELIVERY_ENABLED' in settings
    assert "django.core.mail.backends.dummy.EmailBackend" in settings
    assert 'EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")' in settings
    assert 'EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")' in settings
    assert 'EMAIL_USE_TLS = _env_bool("EMAIL_USE_TLS", False)' in settings
    assert 'EMAIL_USE_SSL = _env_bool("EMAIL_USE_SSL", False)' in settings
    assert 'EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "10"))' in settings


def test_production_only_requires_smtp_when_delivery_is_enabled() -> None:
    settings = SETTINGS.read_text()

    assert "if EMAIL_DELIVERY_ENABLED:" in settings
    assert "email_host in {" in settings
    assert '"mailpit"' in settings
    assert "EMAIL_HOST_USER must be explicitly configured" in settings
    assert "EMAIL_HOST_PASSWORD must be explicitly configured" in settings
    assert "production SMTP must enable EMAIL_USE_TLS or EMAIL_USE_SSL" in settings
    assert "DEFAULT_FROM_EMAIL must be a deliverable sender address" in settings
    assert (
        "ACCOUNT_EMAIL_VERIFICATION_REQUIRED requires EMAIL_DELIVERY_ENABLED"
        in settings
    )


def test_production_compose_defaults_to_no_email_beta_mode() -> None:
    compose = PRODUCTION_COMPOSE.read_text()

    assert "EMAIL_DELIVERY_ENABLED: ${EMAIL_DELIVERY_ENABLED:-0}" in compose
    assert (
        "ACCOUNT_EMAIL_VERIFICATION_REQUIRED: ${ACCOUNT_EMAIL_VERIFICATION_REQUIRED:-0}"
        in compose
    )
    assert "EMAIL_HOST: ${EMAIL_HOST:-}" in compose
    assert "EMAIL_HOST_USER: ${EMAIL_HOST_USER:-}" in compose
    assert "EMAIL_HOST_PASSWORD: ${EMAIL_HOST_PASSWORD:-}" in compose
    assert "EMAIL_USE_TLS: ${EMAIL_USE_TLS:-0}" in compose
    assert "EMAIL_USE_SSL: ${EMAIL_USE_SSL:-0}" in compose


def test_example_environment_documents_no_email_mode_without_a_secret() -> None:
    example = ENV_EXAMPLE.read_text()

    assert "EMAIL_DELIVERY_ENABLED=0" in example
    assert "ACCOUNT_EMAIL_VERIFICATION_REQUIRED=0" in example
    assert "EMAIL_HOST_USER=" in example
    assert "EMAIL_HOST_PASSWORD=" in example
    assert "EMAIL_USE_TLS=0" in example
    assert "EMAIL_USE_SSL=0" in example
    assert "EMAIL_TIMEOUT=10" in example
    assert "replace-me-with-an-smtp-password" not in example
