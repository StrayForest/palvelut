from pathlib import Path

from django.test import RequestFactory

from palvelut.apps.analytics.services import is_synthetic_request

ROOT = Path(__file__).resolve().parents[1]


def test_synthetic_monitor_covers_required_public_journey():
    script = (ROOT / "infra/scripts/synthetic-monitor.sh").read_text()

    assert "SYNTHETIC_BASE_URL" in script
    assert "SYNTHETIC_PROFILE_SLUG" in script
    assert "SYNTHETIC_PROVIDER_ID" in script
    assert "SYNTHETIC_MONITOR_TOKEN" in script
    assert 'check_html "home"' in script
    assert 'check_html "search"' in script
    assert 'check_html "profile"' in script
    assert "check_contact_redirect" in script
    assert "--connect-timeout" in script
    assert "--max-time" in script
    assert "--proto '=https'" in script
    assert "X-Palvelut-Synthetic" in script


def test_synthetic_header_requires_runtime_secret(monkeypatch):
    factory = RequestFactory()

    monkeypatch.setenv("SYNTHETIC_MONITOR_TOKEN", "expected-secret")
    matching = factory.get("/", HTTP_X_PALVELUT_SYNTHETIC="expected-secret")
    wrong = factory.get("/", HTTP_X_PALVELUT_SYNTHETIC="wrong-secret")
    missing = factory.get("/")

    assert is_synthetic_request(matching) is True
    assert is_synthetic_request(wrong) is False
    assert is_synthetic_request(missing) is False


def test_synthetic_classification_is_disabled_without_server_secret(monkeypatch):
    monkeypatch.delenv("SYNTHETIC_MONITOR_TOKEN", raising=False)
    request = RequestFactory().get("/", HTTP_X_PALVELUT_SYNTHETIC="anything")

    assert is_synthetic_request(request) is False


def test_contact_redirect_excludes_authenticated_synthetic_checks_from_funnel():
    contact = (ROOT / "palvelut/apps/discovery/contact.py").read_text()
    analytics = (ROOT / "palvelut/apps/analytics/services.py").read_text()

    assert "if not is_synthetic_request(request):" in contact
    assert "and not is_synthetic_request(request)" in analytics
