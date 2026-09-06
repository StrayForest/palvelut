import json
from pathlib import Path


def test_authenticated_requests_cannot_enter_cdn_cache() -> None:
    rules = json.loads(Path("infra/cloudflare/rules.json").read_text())
    bypass, public = rules["cache_rules"]

    assert bypass["priority"] < public["priority"]
    assert bypass["action"] == "bypass_cache"
    assert (
        'len(http.request.headers["authorization"][0]) gt 0'
        in bypass["expression"]
    )
    assert 'len(http.request.headers["cookie"][0]) gt 0' in bypass["expression"]

    assert public["action"] == "cache_eligible"
    assert public["edge_ttl_mode"] == "respect_origin"
    assert (
        'len(http.request.headers["authorization"][0]) eq 0' in public["expression"]
    )
    assert 'len(http.request.headers["cookie"][0]) eq 0' in public["expression"]

    for protected_prefix in (
        "/palvelut/account/",
        "/palvelut/staff/",
        "/palvelut/report/",
    ):
        assert protected_prefix in bypass["expression"]
        assert protected_prefix in public["expression"]
