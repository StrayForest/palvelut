from pathlib import Path


SETTINGS = Path("palvelut/settings.py")
PRODUCTION_COMPOSE = Path("compose.production.yml")
ENV_EXAMPLE = Path(".env.example")


def test_settings_support_authenticated_secure_smtp() -> None:
    settings = SETTINGS.read_text()

    assert 'EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")' in settings
    assert 'EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")' in settings
    assert 'EMAIL_USE_TLS = _env_bool("EMAIL_USE_TLS", False)' in settings
    assert 'EMAIL_USE_SSL = _env_bool("EMAIL_USE_SSL", False)' in settings
    assert 'EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "10"))' in settings
    assert "EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled" in settings


def test_production_rejects_mailpit_and_missing_smtp_credentials() -> None:
    settings = SETTINGS.read_text()

    assert 'email_host in {"mailpit", "localhost", "127.0.0.1", "::1"}' in settings
    assert "EMAIL_HOST_USER must be explicitly configured" in settings
    assert "EMAIL_HOST_PASSWORD must be explicitly configured" in settings
    assert "production SMTP must enable EMAIL_USE_TLS or EMAIL_USE_SSL" in settings
    assert "DEFAULT_FROM_EMAIL must be a deliverable sender address" in settings


def test_production_compose_passes_smtp_auth_and_transport_settings() -> None:
    compose = PRODUCTION_COMPOSE.read_text()

    assert "EMAIL_HOST_USER: ${EMAIL_HOST_USER:?set EMAIL_HOST_USER}" in compose
    assert (
        "EMAIL_HOST_PASSWORD: ${EMAIL_HOST_PASSWORD:?set EMAIL_HOST_PASSWORD}"
        in compose
    )
    assert "EMAIL_USE_TLS: ${EMAIL_USE_TLS:-1}" in compose
    assert "EMAIL_USE_SSL: ${EMAIL_USE_SSL:-0}" in compose
    assert "EMAIL_TIMEOUT: ${EMAIL_TIMEOUT:-10}" in compose


def test_example_environment_documents_all_smtp_settings_without_a_secret() -> None:
    example = ENV_EXAMPLE.read_text()

    assert "EMAIL_HOST_USER=" in example
    assert "EMAIL_HOST_PASSWORD=" in example
    assert "EMAIL_USE_TLS=0" in example
    assert "EMAIL_USE_SSL=0" in example
    assert "EMAIL_TIMEOUT=10" in example
    assert "replace-me-with-an-smtp-password" not in example
