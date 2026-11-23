import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from app.discovery import DiscoveryRecordError, ingest_results, normalize_result
from app.store import Store


def valid_record(**overrides):
    record = {
        "name": "Example Roofing",
        "email": "info@example.com",
        "city": "Birdseye",
        "vertical": "roofing",
        "service": "AI Website",
        "source_url": "https://example.com/contact",
    }
    record.update(overrides)
    return record


def test_normalize_requires_provider_and_provenance():
    result = normalize_result(valid_record(), "approved-search")
    assert result["source"] == "discovery:approved-search"
    assert result["email"] == "info@example.com"
    with pytest.raises(DiscoveryRecordError):
        normalize_result(valid_record(source_url=""), "approved-search")


@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "http://localhost/admin",
    "http://127.0.0.1/private",
    "https://user:pass@example.com/",
    "https://[::1]/",
])
def test_normalize_rejects_unsafe_source_urls(url):
    with pytest.raises(DiscoveryRecordError):
        normalize_result(valid_record(source_url=url), "approved-search")


def test_ingestion_deduplicates_and_respects_suppressions():
    store = Store(":memory:")
    store.suppress("optout@example.com", "opt-out")
    result = ingest_results(
        store,
        [
            valid_record(),
            valid_record(),
            valid_record(name="Opted out", email="optout@example.com"),
            valid_record(name="", email="bad@example.com"),
        ],
        "approved-search",
    )
    assert result["counts"] == {
        "added": 1, "duplicate": 1, "suppressed": 1, "rejected": 1
    }
    assert len(result["errors"]) == 1


def test_ingestion_has_bounded_batch_size():
    with pytest.raises(DiscoveryRecordError):
        ingest_results(Store(":memory:"), [valid_record()] * 101, "approved-search")
