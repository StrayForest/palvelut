import json
from pathlib import Path


def test_authenticated_requests_cannot_enter_cdn_cache() -> None:
    rules = json.loads(Path("infra/cloudflare/rules.json").read_text())
    bypass, public = rules["cache_rules"]
    auth_present = 'len(http.request.headers["authorization"][0]) gt 0'
    auth_absent = 'len(http.request.headers["authorization"][0]) eq 0'
    cookie_present = 'len(http.request.headers["cookie"][0]) gt 0'
    cookie_absent = 'len(http.request.headers["cookie"][0]) eq 0'
    protected_prefixes = (
        "/palvelut/account/",
        "/palvelut/staff/",
        "/palvelut/report/",
    )

    assert bypass["priority"] < public["priority"]
    assert bypass["action"] == "bypass_cache"
    assert auth_present in bypass["expression"]
    assert cookie_present in bypass["expression"]

    assert public["action"] == "cache_eligible"
    assert public["edge_ttl_mode"] == "respect_origin"
    assert auth_absent in public["expression"]
    assert cookie_absent in public["expression"]

    for protected_prefix in protected_prefixes:
        assert protected_prefix in bypass["expression"]
        assert protected_prefix in public["expression"]
