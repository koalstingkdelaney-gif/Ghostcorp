"""Provider-neutral ingestion boundary for approved public-business search APIs.

This module does not scrape search-engine pages or make network requests.
A separately configured provider adapter supplies structured results; this
boundary validates provenance and normalizes records before they enter CRM.
"""
from __future__ import annotations

from urllib.parse import urlparse
import ipaddress


class DiscoveryRecordError(ValueError):
    """A provider result is missing trustworthy provenance or is malformed."""


def normalize_result(item: dict, provider: str) -> dict:
    if not provider or not provider.strip():
        raise DiscoveryRecordError("provider name is required")
    name = str(item.get("name") or "").strip()
    email = str(item.get("email") or "").strip().lower()
    source_url = str(item.get("source_url") or "").strip()
    if not name:
        raise DiscoveryRecordError("business name is required")
    if not email or "@" not in email or email.startswith("@") or email.endswith("@"):
        raise DiscoveryRecordError("a usable public business email is required")
    parsed = urlparse(source_url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise DiscoveryRecordError("source_url must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password:
        raise DiscoveryRecordError("source_url must not contain credentials")
    host = parsed.hostname.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        raise DiscoveryRecordError("local source URLs are not accepted")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise DiscoveryRecordError("source_url must identify a public host")
    return {
        "name": name[:200],
        "email": email[:320],
        "city": str(item.get("city") or "").strip()[:120],
        "vertical": str(item.get("vertical") or "").strip()[:120],
        "service": str(item.get("service") or "").strip()[:120],
        "source_url": source_url[:2048],
        "source": f"discovery:{provider.strip()[:80]}",
    }


def ingest_results(store, results: list[dict], provider: str) -> dict:
    """Validate and import provider results; dedup/suppress rules stay in Store."""
    if len(results) > 100:
        raise DiscoveryRecordError("maximum 100 records per import")
    counts = {"added": 0, "duplicate": 0, "suppressed": 0, "rejected": 0}
    errors = []
    for index, item in enumerate(results):
        try:
            normalized = normalize_result(item, provider)
            outcome = store.add_lead(normalized)
            counts[outcome] = counts.get(outcome, 0) + 1
        except (DiscoveryRecordError, TypeError, AttributeError) as exc:
            counts["rejected"] += 1
            errors.append({"index": index, "reason": str(exc)})
    store.log("discovery", "provider_import", f"provider={provider}; counts={counts}")
    return {"provider": provider, "counts": counts, "errors": errors}
