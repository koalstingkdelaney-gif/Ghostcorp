import pytest

from scripts.run_worker_loop import positive_int, validate_api_base


def test_worker_limits_accept_safe_values():
    assert positive_int("LIMIT", 20, 1, 200, {"LIMIT": "12"}) == 12


@pytest.mark.parametrize("value", ["0", "-1", "201", "many"])
def test_worker_limits_reject_invalid_values(value):
    with pytest.raises(ValueError):
        positive_int("LIMIT", 20, 1, 200, {"LIMIT": value})


def test_worker_api_allows_loopback_http():
    assert validate_api_base("http://127.0.0.1:8000") == "http://127.0.0.1:8000"


def test_worker_api_requires_https_for_remote_hosts():
    assert validate_api_base("https://ghostcorp.example/api") == "https://ghostcorp.example/api"
    with pytest.raises(ValueError):
        validate_api_base("http://ghostcorp.example")


@pytest.mark.parametrize("value", [
    "https://user:pass@ghostcorp.example",
    "https://ghostcorp.example?token=secret",
    "https://ghostcorp.example#fragment",
])
def test_worker_api_rejects_credentials_query_and_fragment(value):
    with pytest.raises(ValueError):
        validate_api_base(value)
